import json
from test.base import BaseTestCase
from app.models import RoleEnum


class TestRestaurantAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user(username='rest_owner_api', role=RoleEnum.RESTAURANT)

    def test_get_restaurants_api(self):
        self.create_restaurant(self.owner, name='Bún Chả Hà Nội', address='Hoàn Kiếm')
        self.create_restaurant(self.owner, name='Cơm Gà Nha Trang', address='Nha Trang')

        res = self.client.get('/api/restaurants')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['restaurants']), 2)

    def test_get_restaurants_api_search(self):
        self.create_restaurant(self.owner, name='Lẩu Nướng King', address='Hà Nội')
        self.create_restaurant(self.owner, name='Hải Sản Biển Đông', address='Đà Nẵng')

        res = self.client.get('/api/restaurants?name=King')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['restaurants'][0]['name'], 'Lẩu Nướng King')

    def test_restaurant_dashboard_forbidden_for_customer(self):
        customer = self.create_user(username='normal_cust', role=RoleEnum.CUSTOMER)
        self.login_as(customer)

        res = self.client.get('/restaurant/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers['Location'], '/')

    def test_restaurant_dashboard_access_for_owner(self):
        self.create_restaurant(self.owner, name='Quán Của Tôi')
        self.login_as(self.owner)

        res = self.client.get('/restaurant/dashboard')
        self.assertEqual(res.status_code, 200)
