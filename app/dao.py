import bcrypt
from decimal import Decimal
from sqlalchemy import or_
from app import db
from app.models import Restaurant, Dish, User, RoleEnum, Order, OrderStatusEnum, PaymentStatusEnum, Payment, Review, PaymentMethodEnum, Category



def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith('$2a$') or hashed_password.startswith('$2b$') or hashed_password.startswith('$2y$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, password)
    except Exception:
        return False


def auth_user(username, password):
    user = User.query.filter_by(username=username).first()

    if user and verify_password(password, user.password_hash):
        return user

    return None

def check_user_exists(username=None, email=None, phone=None):
    if username and User.query.filter_by(username=username).first():
        return "Tên đăng nhập đã tồn tại!"
    if email and User.query.filter_by(email=email).first():
        return "Email này đã được sử dụng!"
    if phone and User.query.filter_by(phone=phone).first():
        return "Số điện thoại này đã được sử dụng!"
    return None

def add_user(username, password, email, phone=None, address=None, role=RoleEnum.CUSTOMER):
    user = User(
        username=username.strip(),
        password_hash=hash_password(password),
        email=email.strip(),
        phone=phone.strip() if phone else None,
        address=address.strip() if address else None,
        role=role
    )
    db.session.add(user)
    db.session.commit()
    return user

def check_user_update_conflicts(user_id, email=None, phone=None):
    if email:
        existing = User.query.filter(User.email == email.strip(), User.id != user_id).first()
        if existing:
            return "Email này đã được sử dụng bởi tài khoản khác!"
    if phone and phone.strip():
        existing = User.query.filter(User.phone == phone.strip(), User.id != user_id).first()
        if existing:
            return "Số điện thoại này đã được sử dụng bởi tài khoản khác!"
    return None

def update_user_profile(user_id, email, phone=None, address=None, taste_preferences=None, new_password=None):
    user = User.query.get(user_id)
    if not user:
        return None, "Người dùng không tồn tại!"

    if email:
        user.email = email.strip()
    user.phone = phone.strip() if phone and phone.strip() else None
    user.address = address.strip() if address and address.strip() else None
    user.taste_preferences = taste_preferences.strip() if taste_preferences and taste_preferences.strip() else None

    if new_password and new_password.strip():
        user.password_hash = hash_password(new_password.strip())

    db.session.commit()
    return user, None

def get_orders_by_user(user_id, status=None):
    query = Order.query.join(Payment).filter(
        Order.user_id == user_id,
        or_(
            Payment.method == PaymentMethodEnum.CASH,
            Payment.status == PaymentStatusEnum.SUCCESS
        )
    )
    if status and status != 'ALL':
        try:
            status_enum = OrderStatusEnum[status]
            query = query.filter(Order.status == status_enum)
        except KeyError:
            pass
    return query.order_by(Order.created_at.desc()).all()


def get_order_status_counts(user_id):
    orders = Order.query.join(Payment).filter(
        Order.user_id == user_id,
        or_(
            Payment.method == PaymentMethodEnum.CASH,
            Payment.status == PaymentStatusEnum.SUCCESS
        )
    ).all()
    counts = {
        'ALL': len(orders),
        'PENDING': 0,
        'PREPARING': 0,
        'DELIVERING': 0,
        'COMPLETED': 0,
        'CANCELLED': 0
    }
    for o in orders:
        val = o.status.value
        if val in counts:
            counts[val] += 1
        elif val == 'CONFIRMED':
            counts['PREPARING'] += 1
    return counts

def cancel_order(order_id, user_id):
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return False, "Không tìm thấy đơn hàng!"
    if order.status != OrderStatusEnum.PENDING:
        return False, "Chỉ có thể hủy đơn hàng khi đơn đang ở trạng thái Chờ xác nhận!"
    if order.payment and order.payment.status == PaymentStatusEnum.SUCCESS:
        return False, "Đơn hàng đã được thanh toán, không thể hủy!"
    order.status = OrderStatusEnum.CANCELLED
    db.session.commit()
    return True, "Hủy đơn hàng thành công!"

def get_user_by_id(id):
    return User.query.get(id)

def get_restaurant(name=None, address=None, page=1, page_size=6):
    query = Restaurant.query.filter(Restaurant.is_active.is_(True))

    if name and address:
        term = f"%{name.strip()}%"
        addr_term = f"%{address.strip()}%"
        query = query.filter(
            Restaurant.name.ilike(term),
            Restaurant.address.ilike(addr_term)
        )
    elif name:
        term = f"%{name.strip()}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(term),
                Restaurant.address.ilike(term)
            )
        )
    elif address:
        query = query.filter(Restaurant.address.ilike(f"%{address.strip()}%"))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * page_size
    restaurants = query.offset(offset).limit(page_size).all()
    return restaurants, total, total_pages


def get_restaurant_by_id(restaurant_id):
    return Restaurant.query.filter(
        Restaurant.id == restaurant_id,
        Restaurant.is_active.is_(True)
    ).first()


def get_dishes_by_restaurant(restaurant_id):
    return Dish.query.filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_active.is_(True)
    ).all()

def get_all_categories():
    return Category.query.all()


def add_dish(restaurant_id, category_id, name, description, price, image_url, flavor_tags):
    new_dish = Dish(
        restaurant_id=restaurant_id,
        category_id=category_id,
        name=name.strip(),
        description=description.strip() if description else None,
        price=Decimal(price),
        image_url=image_url.strip() if image_url else None,
        flavor_tags=flavor_tags.strip() if flavor_tags else None
    )
    db.session.add(new_dish)
    db.session.commit()
    return new_dish

def get_active_order_for_user(user_id):
    active_statuses = [
        OrderStatusEnum.PENDING,
        OrderStatusEnum.CONFIRMED,
        OrderStatusEnum.PREPARING,
        OrderStatusEnum.DELIVERING
    ]
    return Order.query.join(Payment).filter(
        Order.user_id == user_id,
        Order.status.in_(active_statuses),
        or_(
            Payment.method == PaymentMethodEnum.CASH,
            Payment.status == PaymentStatusEnum.SUCCESS
        )
    ).order_by(Order.id.desc()).first()


def update_restaurant_rating(restaurant_id):
    """Cập nhật lại rating_avg của nhà hàng dựa trên trung bình đánh giá các món ăn"""
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return
    avg_rating = db.session.query(db.func.avg(Review.rating))\
        .join(Dish, Review.dish_id == Dish.id)\
        .filter(Dish.restaurant_id == restaurant_id, Review.is_active == True).scalar()
    restaurant.rating_avg = round(float(avg_rating), 1) if avg_rating is not None else 0.0
    db.session.commit()


def save_or_update_dish_review(user_id, order_id, dish_id, rating, comment=None):
    """Lưu đánh giá món ăn khi đơn hàng đã COMPLETED. Mỗi món trong 1 đơn chỉ được đánh giá đúng 1 lần duy nhất!"""
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return None, "Không tìm thấy thông tin đơn hàng này!"

    if order.status != OrderStatusEnum.COMPLETED:
        return None, "Chỉ có thể đánh giá khi đơn hàng đã giao thành công (Hoàn thành)!"

    item_in_order = any(item.dish_id == dish_id for item in order.items)
    if not item_in_order:
        return None, "Món ăn này không thuộc danh sách món của đơn hàng!"

    dish = Dish.query.get(dish_id)
    if not dish:
        return None, "Món ăn không tồn tại hoặc đã bị xóa!"

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return None, "Số sao đánh giá phải từ 1 đến 5 sao!"
    except (ValueError, TypeError):
        return None, "Số sao đánh giá không hợp lệ!"

    existing_review = Review.query.filter_by(user_id=user_id, order_id=order_id, dish_id=dish_id).first()
    if existing_review:
        return None, "Bạn đã gửi đánh giá cho món ăn này trong đơn hàng rồi! Mỗi món chỉ được đánh giá 1 lần duy nhất."

    clean_comment = comment.strip() if comment else None
    sentiment = round((rating - 1) / 4.0, 2)

    review = Review(
        user_id=user_id,
        order_id=order_id,
        dish_id=dish_id,
        rating=rating,
        comment=clean_comment,
        sentiment_score=sentiment
    )
    db.session.add(review)
    db.session.commit()

    update_restaurant_rating(dish.restaurant_id)

    return review, None


def get_reviews_by_order(order_id):
    """Lấy danh sách đánh giá theo dish_id trong một đơn hàng"""
    reviews = Review.query.filter_by(order_id=order_id, is_active=True).all()
    return {r.dish_id: r for r in reviews}


def get_dish_reviews(dish_id, limit=30):
    """Lấy danh sách các đánh giá của một món ăn kèm thông tin người dùng"""
    return Review.query.filter_by(dish_id=dish_id, is_active=True)\
        .order_by(Review.created_at.desc())\
        .limit(limit)\
        .all()


def get_restaurant_reviews(restaurant_id, limit=50):
    """Lấy danh sách các đánh giá của khách hàng về tất cả các món thuộc nhà hàng"""
    return Review.query.join(Dish, Review.dish_id == Dish.id)\
        .filter(Dish.restaurant_id == restaurant_id, Review.is_active == True)\
        .order_by(Review.created_at.desc())\
        .limit(limit)\
        .all()


def get_restaurant_review_stats(restaurant_id):
    """Lấy thống kê đánh giá của nhà hàng: điểm trung bình và tổng số lượt đánh giá"""
    avg_rating = db.session.query(func.avg(Review.rating))\
        .join(Dish, Review.dish_id == Dish.id)\
        .filter(Dish.restaurant_id == restaurant_id, Review.is_active == True).scalar()
    total_reviews = db.session.query(func.count(Review.id))\
        .join(Dish, Review.dish_id == Dish.id)\
        .filter(Dish.restaurant_id == restaurant_id, Review.is_active == True).scalar()

    return {
        'avg_rating': round(float(avg_rating), 1) if avg_rating is not None else 0.0,
        'total_reviews': total_reviews or 0
    }
