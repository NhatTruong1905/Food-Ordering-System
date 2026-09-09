import os
import hmac
import hashlib
import urllib.parse
from datetime import datetime
from decimal import Decimal
from flask import render_template, request, jsonify, session, redirect, flash
from app import app, dao, login, db
from flask_login import login_user, logout_user, current_user, login_required
from app.utils import get_cart_stats, get_res_total
from app.models import Order, OrderItem, Payment, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum, RoleEnum, \
    Restaurant, Dish
from app.vnpay import build_vnpay_payment_url, verify_vnpay_response, get_vnpay_response_message


@app.context_processor
def inject_cart_stats():
    cart = session.get('cart', {})
    return {
        'cart_stats': get_cart_stats(cart)
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about_view():
    return render_template('about.html')


@app.route('/logout')
def logout_process():
    logout_user()
    return redirect('/login')


@app.route('/login')
def login_view():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('login.html')


@app.route('/login', methods=['post'])
def login_process():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)
        next_url = request.args.get('next')
        return redirect(next_url if next_url else '/')

    flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')
    return redirect('/login')


@app.route('/register')
def register_view():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_process():
    import re
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not username or not email or not phone or not password:
        flash('Vui lòng điền đầy đủ các trường thông tin bắt buộc!', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    if not re.match(r'^[a-zA-Z0-9_.+-]+@gmail\.com$', email):
        flash('Email phải có định dạng Gmail hợp lệ (ví dụ: example@gmail.com)!', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    if not re.match(r'^\d{9,11}$', phone):
        flash('Số điện thoại không hợp lệ (bắt buộc nhập từ 9 đến 11 chữ số, không chứa chữ cái)!', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    if password != confirm_password:
        flash('Mật khẩu xác nhận không trùng khớp!', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    if len(password) < 6:
        flash('Mật khẩu phải có độ dài từ 6 ký tự trở lên!', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    err_msg = dao.check_user_exists(username=username, email=email, phone=phone if phone else None)
    if err_msg:
        flash(err_msg, 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)

    try:
        dao.add_user(
            username=username,
            password=password,
            email=email,
            phone=phone if phone else None,
            address=address if address else None
        )
        flash('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success')
        return redirect('/login')
    except Exception as e:
        flash(f'Đã có lỗi xảy ra trong quá trình đăng ký: {str(e)}', 'danger')
        return render_template('register.html', username=username, email=email, phone=phone, address=address)


@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_view():
    import re
    active_tab = 'tab-info'
    if request.method == 'POST':
        if request.form.get('action') == 'change_password' or request.form.get('current_password') or request.form.get('new_password'):
            active_tab = 'tab-password'

        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        taste_preferences = request.form.get('taste_preferences', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email:
            flash('Địa chỉ email không được để trống!', 'danger')
            orders = dao.get_orders_by_user(current_user.id)
            return render_template('profile.html', user=current_user, orders=orders, active_tab=active_tab)

        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('Địa chỉ email không đúng định dạng!', 'danger')
            orders = dao.get_orders_by_user(current_user.id)
            return render_template('profile.html', user=current_user, orders=orders, active_tab=active_tab)

        if phone and not re.match(r'^\d{9,11}$', phone):
            flash('Số điện thoại không hợp lệ (nhập từ 9 đến 11 chữ số, không chứa chữ cái)!', 'danger')
            orders = dao.get_orders_by_user(current_user.id)
            return render_template('profile.html', user=current_user, orders=orders, active_tab=active_tab)

        conflict_err = dao.check_user_update_conflicts(user_id=current_user.id, email=email,
                                                       phone=phone if phone else None)
        if conflict_err:
            flash(conflict_err, 'danger')
            orders = dao.get_orders_by_user(current_user.id)
            return render_template('profile.html', user=current_user, orders=orders, active_tab=active_tab)

        updated_password = None
        if current_password or new_password or confirm_password:
            if not current_password:
                flash('Vui lòng nhập mật khẩu hiện tại để đổi mật khẩu!', 'danger')
                orders = dao.get_orders_by_user(current_user.id)
                return render_template('profile.html', user=current_user, orders=orders, active_tab='tab-password')

            if not dao.verify_password(current_password, current_user.password_hash):
                flash('Mật khẩu hiện tại không chính xác!', 'danger')
                orders = dao.get_orders_by_user(current_user.id)
                return render_template('profile.html', user=current_user, orders=orders, active_tab='tab-password')

            if len(new_password) < 6:
                flash('Mật khẩu mới phải có tối thiểu 6 ký tự!', 'danger')
                orders = dao.get_orders_by_user(current_user.id)
                return render_template('profile.html', user=current_user, orders=orders, active_tab='tab-password')

            if new_password != confirm_password:
                flash('Mật khẩu mới và xác nhận mật khẩu không trùng khớp!', 'danger')
                orders = dao.get_orders_by_user(current_user.id)
                return render_template('profile.html', user=current_user, orders=orders, active_tab='tab-password')

            updated_password = new_password

        try:
            dao.update_user_profile(
                user_id=current_user.id,
                email=email,
                phone=phone,
                address=address,
                taste_preferences=taste_preferences,
                new_password=updated_password
            )
            if updated_password:
                flash('Đổi mật khẩu thành công!', 'success')
            else:
                flash('Cập nhật thông tin hồ sơ thành công!', 'success')
            return redirect('/profile')
        except Exception as e:
            flash(f'Lỗi khi cập nhật hồ sơ: {str(e)}', 'danger')
            orders = dao.get_orders_by_user(current_user.id)
            return render_template('profile.html', user=current_user, orders=orders, active_tab=active_tab)

    orders = dao.get_orders_by_user(current_user.id)
    return render_template('profile.html', user=current_user, orders=orders, active_tab='tab-info')


@app.route('/orders')
@login_required
def orders_view():
    status = request.args.get('status', 'ALL').strip().upper()
    orders = dao.get_orders_by_user(current_user.id, status=status)
    counts = dao.get_order_status_counts(current_user.id)
    return render_template('orders.html', orders=orders, current_status=status, counts=counts)


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order_api(order_id):
    success, message = dao.cancel_order(order_id, current_user.id)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400


@app.route('/api/restaurants', methods=['GET'])
def restaurants():
    try:
        name = request.args.get('name', '').strip()
        address = request.args.get('address', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 6, type=int)

        restaurants_list, total_count, total_pages = dao.get_restaurant(
            name=name if name else None,
            address=address if address else None,
            page=page,
            page_size=page_size
        )

        data = []
        for r in restaurants_list:
            data.append({
                'id': r.id,
                'name': r.name,
                'address': r.address if r.address else None,
                'description': r.description if r.description else None,
                'image_url': r.image_url if r.image_url else None,
                'phone': r.owner.phone if (hasattr(r, 'owner') and r.owner and r.owner.phone) else None,
                'latitude': r.latitude if r.latitude is not None else None,
                'longitude': r.longitude if r.longitude is not None else None,
                'rating_avg': r.rating_avg if (r.rating_avg is not None and r.rating_avg > 0) else None
            })

        return jsonify({
            'status': 'success',
            'restaurants': data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }), 200

    except Exception as err:
        return jsonify({
            'status': 'error',
            'error': str(err),
        }), 400


@app.route('/api/restaurants/<int:restaurant_id>/dishes', methods=['GET'])
def restaurant_dishes(restaurant_id):
    try:
        restaurant = dao.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            return jsonify({
                'status': 'error',
                'message': 'Nhà hàng không tồn tại'
            }), 404

        dishes_list = dao.get_dishes_by_restaurant(restaurant_id)
        data = []
        for d in dishes_list:
            price_val = float(d.price) if d.price else 0.0
            price_formatted = f"{int(price_val):,} VNĐ".replace(",", ".")
            data.append({
                'id': d.id,
                'restaurant_id': d.restaurant_id,
                'category_name': d.category.name if d.category else 'Món ngon',
                'name': d.name,
                'description': d.description if d.description else None,
                'price': price_val,
                'price_formatted': price_formatted,
                'image_url': d.image_url if d.image_url else None,
                'flavor_tags': d.flavor_tags if d.flavor_tags else None
            })

        return jsonify({
            'status': 'success',
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'rating_avg': restaurant.rating_avg
            },
            'dishes': data,
            'total': len(data)
        }), 200

    except Exception as err:
        return jsonify({
            'status': 'error',
            'error': str(err),
        }), 400


@app.route('/cart')
def cart_view():
    cart = session.get('cart', {})
    if cart:
        changed = False
        valid_res_ids = {r.id for r in Restaurant.query.filter(Restaurant.id.in_([int(k) for k in cart.keys() if k.isdigit()])).all()}
        for k in list(cart.keys()):
            if not k.isdigit() or int(k) not in valid_res_ids:
                del cart[k]
                changed = True
        if changed:
            session['cart'] = cart
            session.modified = True
    cart_stats = get_cart_stats(cart)
    return render_template('cart.html', cart_stats=cart_stats)


@app.route('/api/carts', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        restaurant_id = str(data.get("restaurant_id"))
        dish_id = str(data.get("dish_id"))

        dish_name = data.get("name") or data.get("dish_name") or "Món ăn"
        dish_price = float(data.get("price") or data.get("dish_price") or 0)

        cart = session.get('cart', {})

        if restaurant_id not in cart:
            cart[restaurant_id] = {"restaurant_id": restaurant_id, "items": {}}

        res_items = cart[restaurant_id]["items"]

        if dish_id in res_items:
            res_items[dish_id]['quantity'] += 1
        else:
            res_items[dish_id] = {
                "id": dish_id,
                "name": dish_name,
                "price": dish_price,
                "quantity": 1
            }

        session['cart'] = cart
        session.modified = True
        return jsonify({"message": "Thành công!", "stats": get_cart_stats(cart)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/carts/<restaurant_id>/<dish_id>', methods=['PUT'])
def update_cart(restaurant_id, dish_id):
    try:
        data = request.get_json()
        quantity = int(data.get("quantity", 1))
        cart = session.get('cart', {})

        if restaurant_id in cart and dish_id in cart[restaurant_id]["items"]:
            if quantity > 0:
                cart[restaurant_id]["items"][dish_id]['quantity'] = quantity
            else:
                del cart[restaurant_id]["items"][dish_id]
                if not cart[restaurant_id]["items"]:
                    del cart[restaurant_id]

            session['cart'] = cart
            session.modified = True

        item_subtotal = 0
        if restaurant_id in cart and dish_id in cart[restaurant_id]["items"]:
            item = cart[restaurant_id]["items"][dish_id]
            item_subtotal = item['quantity'] * item['price']

        res_data = get_cart_stats(cart)

        return jsonify({
            "item_subtotal": item_subtotal,
            "res_total_amount": get_res_total(cart, restaurant_id),
            "grand_total_quantity": res_data['total_quantity'],
            "grand_total_amount": res_data['total_amount']
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/carts/<restaurant_id>/<dish_id>', methods=['DELETE'])
def delete_cart(restaurant_id, dish_id):
    try:
        cart = session.get('cart', {})

        if restaurant_id in cart and dish_id in cart[restaurant_id]["items"]:
            del cart[restaurant_id]["items"][dish_id]
            if not cart[restaurant_id]["items"]:
                del cart[restaurant_id]

            session['cart'] = cart
            session.modified = True

        res_data = get_cart_stats(cart)
        res_items_left = len(cart[restaurant_id]["items"]) if restaurant_id in cart else 0

        return jsonify({
            "res_items_left": res_items_left,
            "res_total_amount": get_res_total(cart, restaurant_id),
            "grand_total_quantity": res_data['total_quantity'],
            "grand_total_amount": res_data['total_amount']
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return "Đã xóa sạch giỏ hàng cũ! <a href='/cart'>Quay lại giỏ hàng</a>"


@app.route('/api/checkout/<int:restaurant_id>', methods=['POST'])
def checkout_restaurant(restaurant_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Vui lòng đăng nhập để đặt hàng!"}), 401

    try:
        cart = session.get('cart', {})
        res_id_str = str(restaurant_id)

        if res_id_str not in cart or not cart[res_id_str].get('items'):
            return jsonify({"error": "Nhà hàng này không có món nào trong giỏ!"}), 400

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            if res_id_str in cart:
                del cart[res_id_str]
                session['cart'] = cart
                session.modified = True
            return jsonify({"error": "Nhà hàng này không còn tồn tại hoặc dữ liệu vừa được làm mới. Vui lòng chọn món lại!"}), 400

        data = request.get_json() or {}
        delivery_address = data.get('delivery_address', "")

        if not delivery_address.strip():
            return jsonify({"error": "Vui lòng cung cấp địa chỉ giao hàng!"}), 400

        payment_method_str = data.get('payment_method', 'CASH')
        try:
            payment_method = PaymentMethodEnum[payment_method_str]
        except KeyError:
            payment_method = PaymentMethodEnum.CASH

        items_data = cart[res_id_str]['items']
        for dish_id, item in items_data.items():
            if not Dish.query.get(int(dish_id)):
                if res_id_str in cart:
                    del cart[res_id_str]
                    session['cart'] = cart
                    session.modified = True
                return jsonify({"error": f"Món '{item.get('name', '')}' không còn tồn tại trong hệ thống. Vui lòng chọn lại món!"}), 400

        total_amount = sum(item['quantity'] * item['price'] for item in items_data.values())

        new_order = Order(
            user_id=current_user.id,
            restaurant_id=restaurant_id,
            total_amount=Decimal(total_amount),
            status=OrderStatusEnum.PENDING,
            delivery_address=delivery_address.strip()
        )
        db.session.add(new_order)
        db.session.flush()

        for dish_id, item in items_data.items():
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=int(dish_id),
                quantity=item['quantity'],
                price_at_purchase=Decimal(item['price'])
            )
            db.session.add(order_item)

        new_payment = Payment(
            order_id=new_order.id,
            amount=Decimal(total_amount),
            method=payment_method,
            status=PaymentStatusEnum.PENDING
        )
        db.session.add(new_payment)

        del cart[res_id_str]
        session['cart'] = cart
        session.modified = True

        db.session.commit()

        res_stats = get_cart_stats(cart)

        if payment_method == PaymentMethodEnum.VNPAY:
            return_url = request.host_url.rstrip('/') + '/vnpay_return'
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            payment_url = build_vnpay_payment_url(new_order, client_ip, return_url)
            return jsonify({
                "status": "success",
                "payment_method": "VNPAY",
                "payment_url": payment_url,
                "order_id": new_order.id,
                "restaurant_name": new_order.restaurant.name if new_order.restaurant else "Nhà hàng",
                "restaurant_image": (new_order.restaurant.image_url if new_order.restaurant and new_order.restaurant.image_url else '/static/images/storefront.jpg'),
                "total_amount": float(new_order.total_amount),
                "message": "Đặt hàng thành công! Vui lòng hoàn tất thanh toán.",
                "grand_total_quantity": res_stats['total_quantity'],
                "grand_total_amount": res_stats['total_amount']
            }), 200

        return jsonify({
            "status": "success",
            "payment_method": "CASH",
            "message": f"Đặt hàng thành công! Mã đơn hàng: #{new_order.id}",
            "order_id": new_order.id,
            "restaurant_name": new_order.restaurant.name if new_order.restaurant else "Nhà hàng",
            "restaurant_image": (new_order.restaurant.image_url if new_order.restaurant and new_order.restaurant.image_url else '/static/images/storefront.jpg'),
            "grand_total_quantity": res_stats['total_quantity'],
            "grand_total_amount": res_stats['total_amount']
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/restaurant/dashboard')
@login_required
def restaurant_dashboard():
    if current_user.role != RoleEnum.RESTAURANT:
        flash("Bạn không có quyền truy cập trang quản lý nhà hàng.", "danger")
        return redirect('/')

    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if not restaurant:
        return "Tài khoản của bạn chưa được liên kết với nhà hàng nào.", 404

    orders = Order.query.filter_by(restaurant_id=restaurant.id) \
        .order_by(Order.created_at.desc()).all()

    return render_template('restaurant_dashboard.html', restaurant=restaurant, orders=orders)


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    if current_user.role != RoleEnum.RESTAURANT:
        return jsonify({"error": "Không có quyền thực hiện thao tác này"}), 403

    data = request.get_json()
    new_status_str = data.get('status')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

    if order.restaurant.owner_id != current_user.id:
        return jsonify({"error": "Đơn hàng này không thuộc nhà hàng của bạn"}), 403

    try:
        new_status = OrderStatusEnum[new_status_str]
        order.status = new_status
        db.session.commit()
        return jsonify(
            {"status": "success", "message": f"Đã cập nhật trạng thái đơn #{order.id} thành {new_status.value}"}), 200
    except KeyError:
        return jsonify({"error": "Trạng thái không hợp lệ"}), 400


@app.route('/vnpay_return')
def vnpay_return():
    query_params = request.args.to_dict()
    is_valid = verify_vnpay_response(query_params)

    txn_ref = query_params.get('vnp_TxnRef', '')
    response_code = query_params.get('vnp_ResponseCode', '')
    transaction_no = query_params.get('vnp_TransactionNo', '')
    bank_code = query_params.get('vnp_BankCode', '')
    amount_str = query_params.get('vnp_Amount', '0')
    pay_date_str = query_params.get('vnp_PayDate', '')
    order_info = query_params.get('vnp_OrderInfo', '')

    order_id = None
    if txn_ref:
        try:
            order_id = int(txn_ref.split('_')[0])
        except (ValueError, IndexError):
            order_id = None

    order = Order.query.get(order_id) if order_id else None
    payment = order.payment if order else None

    try:
        amount = float(amount_str) / 100 if amount_str else 0
    except ValueError:
        amount = 0

    pay_date = None
    if pay_date_str and len(pay_date_str) == 14:
        try:
            pay_date = datetime.strptime(pay_date_str, '%Y%m%d%H%M%S')
        except ValueError:
            pay_date = None

    is_success = False
    message = get_vnpay_response_message(response_code)

    if is_valid:
        if response_code == '00':
            is_success = True
            if payment:
                payment.status = PaymentStatusEnum.SUCCESS
                try:
                    payment.transaction_id = transaction_no
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    payment.transaction_id = f"{transaction_no}_{order.id if order else '0'}_{int(datetime.now().timestamp())}"
                    db.session.commit()
        else:
            if payment and payment.status != PaymentStatusEnum.SUCCESS:
                payment.status = PaymentStatusEnum.FAILED
                try:
                    payment.transaction_id = transaction_no
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    payment.transaction_id = f"{transaction_no}_{order.id if order else '0'}_{int(datetime.now().timestamp())}"
                    db.session.commit()
    else:
        message = "Chữ ký bảo mật không hợp lệ (Dữ liệu giao dịch có thể đã bị can thiệp)."

    return render_template(
        'vnpay_result.html',
        is_success=is_success,
        is_valid=is_valid,
        order=order,
        order_id=order_id,
        payment=payment,
        transaction_no=transaction_no,
        bank_code=bank_code,
        amount=amount,
        pay_date=pay_date,
        order_info=order_info,
        message=message,
        response_code=response_code
    )


@app.route('/api/orders/<int:order_id>/pay_vnpay', methods=['POST'])
@login_required
def retry_vnpay_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng!"}), 404
    if order.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        return jsonify({"error": "Bạn không có quyền thanh toán đơn hàng này!"}), 403
    if order.status == OrderStatusEnum.CANCELLED:
        return jsonify({"error": "Đơn hàng này đã bị hủy, không thể thanh toán!"}), 400
    if order.payment and order.payment.status == PaymentStatusEnum.SUCCESS:
        return jsonify({"error": "Đơn hàng này đã được thanh toán thành công trước đó!"}), 400

    if not order.payment:
        new_payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            method=PaymentMethodEnum.VNPAY,
            status=PaymentStatusEnum.PENDING
        )
        db.session.add(new_payment)
        db.session.commit()
    else:
        order.payment.method = PaymentMethodEnum.VNPAY
        order.payment.status = PaymentStatusEnum.PENDING
        db.session.commit()

    return_url = request.host_url.rstrip('/') + '/vnpay_return'
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    payment_url = build_vnpay_payment_url(order, client_ip, return_url)

    return jsonify({
        "status": "success",
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "payment_url": payment_url,
        "message": "Đã tạo liên kết thanh toán VNPAY!"
    }), 200


@app.route('/api/orders/<int:order_id>/confirm_payment', methods=['POST'])
@login_required
def confirm_order_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng!"}), 404
    if order.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        return jsonify({"error": "Bạn không có quyền thực hiện thao tác này!"}), 403
    if order.status == OrderStatusEnum.CANCELLED:
        return jsonify({"error": "Đơn hàng này đã bị hủy!"}), 400

    if order.payment:
        order.payment.status = PaymentStatusEnum.SUCCESS
        if not order.payment.transaction_id:
            order.payment.transaction_id = f"TRANSFER_{order.id}_{int(datetime.now().timestamp())}"
    else:
        new_payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            method=PaymentMethodEnum.VNPAY,
            status=PaymentStatusEnum.SUCCESS,
            transaction_id=f"TRANSFER_{order.id}_{int(datetime.now().timestamp())}"
        )
        db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Đã xác nhận thanh toán thành công cho đơn hàng #{order.id}!"
    }), 200


@app.route('/api/orders/<int:order_id>/pay_vnpay_test', methods=['POST'])
@login_required
def pay_vnpay_test(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng!"}), 404
    if order.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        return jsonify({"error": "Bạn không có quyền thanh toán đơn hàng này!"}), 403
    if order.status == OrderStatusEnum.CANCELLED:
        return jsonify({"error": "Đơn hàng này đã bị hủy, không thể thanh toán!"}), 400

    req_data = request.get_json(silent=True) or {}
    card_number = req_data.get('card_number', '').replace(' ', '').strip()
    card_holder = req_data.get('card_holder', '').strip().upper()
    issue_date = req_data.get('issue_date', '').strip()
    otp = req_data.get('otp', '').strip()

    if card_number and card_number != '9704198526191432198':
        return jsonify({"error": "Số thẻ không đúng! Thẻ thử nghiệm NCB là: 9704198526191432198"}), 400
    if card_holder and card_holder != 'NGUYEN VAN A':
        return jsonify({"error": "Tên chủ thẻ không đúng! Chủ thẻ thử nghiệm là: NGUYEN VAN A"}), 400
    if issue_date and issue_date != '07/15':
        return jsonify({"error": "Ngày phát hành không đúng! Ngày phát hành thử nghiệm là: 07/15"}), 400
    if otp and otp != '123456':
        return jsonify({"error": "Mã OTP không chính xác! Mã OTP thử nghiệm là: 123456"}), 400

    now = datetime.now()
    now_str = now.strftime('%Y%m%d%H%M%S')
    txn_no = f"1455{int(now.timestamp()) % 100000}"

    if not order.payment:
        new_payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            method=PaymentMethodEnum.VNPAY,
            status=PaymentStatusEnum.SUCCESS,
            transaction_id=txn_no
        )
        db.session.add(new_payment)
    else:
        order.payment.method = PaymentMethodEnum.VNPAY
        order.payment.status = PaymentStatusEnum.SUCCESS
        order.payment.transaction_id = txn_no
    db.session.commit()

    query_params = {
        'vnp_Amount': str(int(float(order.total_amount) * 100)),
        'vnp_BankCode': 'NCB',
        'vnp_BankTranNo': f'VNP{txn_no}',
        'vnp_CardType': 'ATM',
        'vnp_OrderInfo': f'Thanh toan don hang {order.id} tai Food Shoppe',
        'vnp_PayDate': now_str,
        'vnp_ResponseCode': '00',
        'vnp_TmnCode': os.getenv('VNPAY_TMN_CODE', '1SI5X77N'),
        'vnp_TransactionNo': txn_no,
        'vnp_TransactionStatus': '00',
        'vnp_TxnRef': f'{order.id}_{int(now.timestamp())}'
    }

    sorted_p = sorted(query_params.items())
    hash_data = '&'.join(f'{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}' for k, v in sorted_p)
    hash_secret = os.getenv('VNPAY_HASH_SECRET') or os.getenv('vnp_HashSecret') or 'QPYBOSLUIPUJDYHYIVHZBMRKXEAGWYJD'
    secure_hash = hmac.new(hash_secret.encode('utf-8'), hash_data.encode('utf-8'), hashlib.sha512).hexdigest()

    redirect_url = f'/vnpay_return?{hash_data}&vnp_SecureHash={secure_hash}'

    return jsonify({
        "status": "success",
        "message": "Thanh toán bằng thẻ test VNPAY (NGUYEN VAN A) thành công!",
        "redirect_url": redirect_url
    }), 200


@app.route('/api/chat/active_order', methods=['GET'])
def get_active_chat_order():
    if not current_user.is_authenticated:
        return jsonify({"active": False})

    order = dao.get_active_order_for_user(current_user.id)
    if not order:
        return jsonify({"active": False})

    restaurant = order.restaurant
    return jsonify({
        "active": True,
        "order_id": order.id,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "restaurant_image": restaurant.image_url or '/static/images/storefront.jpg',
        "order_status": order.status.value,
        "created_at": order.created_at.strftime('%H:%M | %d/%m/%Y')
    })


@app.route('/api/chat/<int:order_id>/messages', methods=['GET'])
@login_required
def get_order_chat_messages(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng!"}), 404

    is_customer = (order.user_id == current_user.id)
    is_owner = (order.restaurant.owner_id == current_user.id)
    is_admin = (current_user.role == RoleEnum.ADMIN)

    if not (is_customer or is_owner or is_admin):
        return jsonify({"error": "Bạn không có quyền xem cuộc trò chuyện này!"}), 403

    after_id = request.args.get('after_id', type=int)
    messages = dao.get_chat_messages(order_id, after_id=after_id)
    dao.mark_chat_messages_read(order_id, current_user.id)

    msg_list = []
    for m in messages:
        msg_list.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.username,
            "is_me": (m.sender_id == current_user.id),
            "is_restaurant": (m.sender_id == order.restaurant.owner_id),
            "message": m.message,
            "created_at": m.created_at.strftime('%H:%M')
        })

    return jsonify({
        "status": "success",
        "order_id": order.id,
        "restaurant_name": order.restaurant.name,
        "restaurant_image": order.restaurant.image_url or '/static/images/storefront.jpg',
        "customer_name": order.customer.username,
        "messages": msg_list
    })


@app.route('/api/chat/<int:order_id>/send', methods=['POST'])
@login_required
def send_order_chat_message(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng!"}), 404

    is_customer = (order.user_id == current_user.id)
    is_owner = (order.restaurant.owner_id == current_user.id)
    is_admin = (current_user.role == RoleEnum.ADMIN)

    if not (is_customer or is_owner or is_admin):
        return jsonify({"error": "Bạn không có quyền gửi tin nhắn trong đơn này!"}), 403

    data = request.get_json(silent=True) or {}
    text = (data.get('message') or '').strip()
    if not text:
        return jsonify({"error": "Nội dung tin nhắn không được để trống!"}), 400

    new_msg = dao.add_chat_message(order_id, current_user.id, text)

    return jsonify({
        "status": "success",
        "message": {
            "id": new_msg.id,
            "sender_id": new_msg.sender_id,
            "sender_name": current_user.username,
            "is_me": True,
            "is_restaurant": (new_msg.sender_id == order.restaurant.owner_id),
            "message": new_msg.message,
            "created_at": new_msg.created_at.strftime('%H:%M')
        }
    })
