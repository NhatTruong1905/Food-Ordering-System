import bcrypt
from sqlalchemy import or_
from app import db
from app.models import Restaurant, Dish, User, RoleEnum, Order, OrderStatusEnum, PaymentStatusEnum, Payment


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
    query = Order.query.filter_by(user_id=user_id)
    if status and status != 'ALL':
        try:
            status_enum = OrderStatusEnum[status]
            query = query.filter(Order.status == status_enum)
        except KeyError:
            pass
    return query.order_by(Order.created_at.desc()).all()

def get_order_status_counts(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
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
        Payment.status == PaymentStatusEnum.SUCCESS
    ).order_by(Order.id.desc()).first()



