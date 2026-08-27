import hashlib
from sqlalchemy import or_
from werkzeug.security import check_password_hash
from app.models import Restaurant, Dish, User


def auth_user(username, password):
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        return user

    return None

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
