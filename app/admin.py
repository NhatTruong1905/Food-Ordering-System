from flask import redirect, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app import app, db
from app.models import Category, Dish, Order, Payment, Restaurant, Review, RoleEnum, User

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(f'/login?next={request.url}')

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or current_user.role != RoleEnum.ADMIN:
            return redirect(f'/login?next={request.url}')
        return super(MyAdminIndexView, self).index()

class UserView(AuthenticatedModelView):
    column_searchable_list = ['username', 'email', 'phone']
    column_filters = ['role', 'is_active']
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash', 'orders', 'reviews', 'cart', 'restaurants']

class RestaurantView(AuthenticatedModelView):
    column_searchable_list = ['name', 'address']
    column_filters = ['is_active', 'rating_avg']

class DishView(AuthenticatedModelView):
    column_searchable_list = ['name', 'flavor_tags']
    column_filters = ['price', 'restaurant_id']

class OrderView(AuthenticatedModelView):
    column_searchable_list = ['delivery_address']
    column_filters = ['status', 'created_at']
    
admin = Admin(app, name='Quản Trị', index_view=MyAdminIndexView(url='/admin'))

admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(RestaurantView(Restaurant, db.session, name='Nhà hàng'))
admin.add_view(AuthenticatedModelView(Category, db.session, name='Danh mục món'))
admin.add_view(DishView(Dish, db.session, name='Món ăn'))
admin.add_view(OrderView(Order, db.session, name='Đơn hàng'))
admin.add_view(AuthenticatedModelView(Payment, db.session, name='Thanh toán'))
admin.add_view(AuthenticatedModelView(Review, db.session, name='Đánh giá'))