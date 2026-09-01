import bcrypt
from sqlalchemy import or_
from app import db
from app.models import Restaurant, Dish, User, RoleEnum


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

def add_user(username, password, email, phone=None, role=RoleEnum.CUSTOMER):
    user = User(
        username=username.strip(),
        password_hash=hash_password(password),
        email=email.strip(),
        phone=phone.strip() if phone else None,
        role=role
    )
    db.session.add(user)
    db.session.commit()
    return user

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
