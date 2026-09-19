from flask import redirect, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from sqlalchemy import func

from app import app, db
from app.models import Category, Dish, Order, Payment, Restaurant, Review, RoleEnum, User

class AdminOnlyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

    def is_visible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(f'/login?next={request.url}')

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in [RoleEnum.ADMIN, RoleEnum.RESTAURANT]

    def inaccessible_callback(self, name, **kwargs):
        return redirect(f'/login?next={request.url}')

    @expose('/')
    def index(self):
        if not self.is_accessible():
            return redirect(f'/login?next={request.url}')
        return super(MyAdminIndexView, self).index()

class UserView(AdminOnlyModelView):
    column_searchable_list = ['username', 'email', 'phone']
    column_filters = ['role', 'is_active']
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash', 'orders', 'reviews', 'cart', 'restaurants']

class RestaurantView(ModelView):
    column_searchable_list = ['name', 'address']
    column_filters = ['is_active', 'rating_avg']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in [RoleEnum.ADMIN, RoleEnum.RESTAURANT]

    def is_visible(self):
        return current_user.is_authenticated and current_user.role in [RoleEnum.ADMIN, RoleEnum.RESTAURANT]

    def inaccessible_callback(self, name, **kwargs):
        return redirect(f'/login?next={request.url}')

    def get_query(self):
        if current_user.role == RoleEnum.RESTAURANT:
            return self.session.query(self.model).filter(self.model.owner_id == current_user.id)
        return super(RestaurantView, self).get_query()

    def get_count_query(self):
        if current_user.role == RoleEnum.RESTAURANT:
            return self.session.query(func.count(self.model.id)).filter(self.model.owner_id == current_user.id)
        return super(RestaurantView, self).get_count_query()

    @property
    def can_create(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

    @property
    def can_delete(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

class DishView(ModelView):
    column_searchable_list = ['name', 'flavor_tags']
    column_filters = ['price', 'restaurant_id']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in [RoleEnum.ADMIN, RoleEnum.RESTAURANT]

    def is_visible(self):
        return current_user.is_authenticated and current_user.role in [RoleEnum.ADMIN, RoleEnum.RESTAURANT]

    def inaccessible_callback(self, name, **kwargs):
        return redirect(f'/login?next={request.url}')

    def get_query(self):
        if current_user.role == RoleEnum.RESTAURANT:
            res = Restaurant.query.filter_by(owner_id=current_user.id).first()
            res_id = res.id if res else -1
            return self.session.query(self.model).filter(self.model.restaurant_id == res_id)
        return super(DishView, self).get_query()

    def get_count_query(self):
        if current_user.role == RoleEnum.RESTAURANT:
            res = Restaurant.query.filter_by(owner_id=current_user.id).first()
            res_id = res.id if res else -1
            return self.session.query(func.count(self.model.id)).filter(self.model.restaurant_id == res_id)
        return super(DishView, self).get_count_query()

    def on_model_change(self, form, model, is_created):
        if current_user.role == RoleEnum.RESTAURANT:
            res = Restaurant.query.filter_by(owner_id=current_user.id).first()
            if res:
                model.restaurant_id = res.id

    def create_form(self, obj=None):
        form = super(DishView, self).create_form(obj)
        if current_user.role == RoleEnum.RESTAURANT:
            form.restaurant.query = Restaurant.query.filter_by(owner_id=current_user.id)
        return form

    def edit_form(self, obj=None):
        form = super(DishView, self).edit_form(obj)
        if current_user.role == RoleEnum.RESTAURANT:
            form.restaurant.query = Restaurant.query.filter_by(owner_id=current_user.id)
        return form

class OrderView(AdminOnlyModelView):
    column_searchable_list = ['delivery_address']
    column_filters = ['status', 'created_at']

admin = Admin(app, name='Quản Trị', index_view=MyAdminIndexView(url='/admin'))

admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(RestaurantView(Restaurant, db.session, name='Nhà hàng'))
admin.add_view(AdminOnlyModelView(Category, db.session, name='Danh mục món'))
admin.add_view(DishView(Dish, db.session, name='Món ăn'))
admin.add_view(OrderView(Order, db.session, name='Đơn hàng'))
admin.add_view(AdminOnlyModelView(Payment, db.session, name='Thanh toán'))
admin.add_view(AdminOnlyModelView(Review, db.session, name='Đánh giá'))

from flask_admin.menu import MenuLink

admin.add_link(MenuLink(name='Về trang chủ', url='/'))
admin.add_link(MenuLink(name='Đăng xuất', url='/logout'))