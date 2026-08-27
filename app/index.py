from flask import render_template, request, jsonify, session, redirect
from app import app, dao, login
from flask_login import login_user, logout_user, current_user

from app.utils import get_cart_stats, get_res_total


@app.route('/')
def index():
    print("current_user:", current_user)
    print("authenticated:", current_user.is_authenticated)

    return render_template('index.html')

@app.route('/logout')
def logout_process():
    logout_user()
    return redirect('/login')

@app.route('/login')
def login_view():
    return render_template('login.html')

@app.route('/login', methods=['post'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    next = request.args.get('next')
    return redirect(next if next else '/')

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

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


@app.route('/api/checkout/<restaurant_id>', methods=['POST'])
def checkout_restaurant(restaurant_id):
    try:
        cart = session.get('cart', {})
        restaurant_id = str(restaurant_id)

        if restaurant_id not in cart or not cart[restaurant_id].get('items'):
            return jsonify({"error": "Nhà hàng này không có món nào trong giỏ!"}), 400

        # Lấy dữ liệu món ăn của riêng nhà hàng này
        # res_cart_data = cart[restaurant_id]

        # Lưu đơn hàng
        # ví dụ: save_order_to_db(user_id=current_user.id, restaurant_id=restaurant_id, items=res_cart_data['items'])

        del cart[restaurant_id]
        session['cart'] = cart
        session.modified = True

        res_data = get_cart_stats(cart)
        return jsonify({
            "message": f"Đặt hàng thành công cho Nhà hàng #{restaurant_id}!",
            "grand_total_quantity": res_data['total_quantity'],
            "grand_total_amount": res_data['total_amount']
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return "Đã xóa sạch giỏ hàng cũ! <a href='/cart'>Quay lại giỏ hàng</a>"