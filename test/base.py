import unittest
from decimal import Decimal
from sqlalchemy.pool import StaticPool
from app import app, db, dao, index
from app.models import (
    User, RoleEnum, Restaurant, Category, Dish, Order, OrderItem,
    Payment, PaymentMethodEnum, PaymentStatusEnum, OrderStatusEnum, Review
)
from app.dao import hash_password

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = 'test-secret-key-for-unittests'

_test_engine = db._make_engine(
    None,
    {
        'url': 'sqlite:///:memory:',
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    },
    app
)
db._app_engines[app] = {None: _test_engine}


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_as(self, user, password='password123'):
        self.client.post('/login', data={'username': user.username, 'password': password})

    def logout(self):
        self.client.get('/logout')

    def create_user(self, username='testuser', password='password123', email=None, phone=None, address=None, role=RoleEnum.CUSTOMER):
        email = email or f"{username}@test.com"
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email,
            phone=phone,
            address=address,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user

    def create_restaurant(self, owner, name='Quán Ăn Ngon', address='123 Nguyễn Huệ, Q1', is_active=True):
        restaurant = Restaurant(
            owner_id=owner.id,
            name=name,
            address=address,
            is_active=is_active,
            rating_avg=5.0
        )
        db.session.add(restaurant)
        db.session.commit()
        return restaurant

    def create_category(self, name='Món chính'):
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        return category

    def create_dish(self, restaurant, category, name='Cơm tấm sườn nướng', price=45000, is_active=True):
        dish = Dish(
            restaurant_id=restaurant.id,
            category_id=category.id,
            name=name,
            price=Decimal(str(price)),
            is_active=is_active
        )
        db.session.add(dish)
        db.session.commit()
        return dish

    def create_order(self, user, restaurant, items=None, total_amount=45000,
                     status=OrderStatusEnum.PENDING, payment_method=PaymentMethodEnum.CASH,
                     payment_status=PaymentStatusEnum.PENDING, delivery_address='123 Test Street'):
        order = Order(
            user_id=user.id,
            restaurant_id=restaurant.id,
            total_amount=Decimal(str(total_amount)),
            status=status,
            delivery_address=delivery_address
        )
        db.session.add(order)
        db.session.flush()

        if items:
            for dish, qty, price in items:
                oi = OrderItem(
                    order_id=order.id,
                    dish_id=dish.id,
                    quantity=qty,
                    price_at_purchase=Decimal(str(price))
                )
                db.session.add(oi)

        payment = Payment(
            order_id=order.id,
            amount=Decimal(str(total_amount)),
            method=payment_method,
            status=payment_status
        )
        db.session.add(payment)
        db.session.commit()
        return order
