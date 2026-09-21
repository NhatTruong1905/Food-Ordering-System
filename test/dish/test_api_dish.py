from test.base import BaseTestCase
from app.models import RoleEnum, Dish


class TestDishAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user(username='dish_api_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Nhà Hàng Hương Sen')
        self.category = self.create_category(name='Đồ Uống')

    def test_get_restaurant_dishes_api(self):
        self.create_dish(self.restaurant, self.category, name='Trà Đào Cam Sả', price=25000)
        self.create_dish(self.restaurant, self.category, name='Trà Sữa Trân Châu', price=30000)

        res = self.client.get(f'/api/restaurants/{self.restaurant.id}/dishes')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total'], 2)
        names = [d['name'] for d in data['dishes']]
        self.assertIn('Trà Đào Cam Sả', names)
        self.assertIn('Trà Sữa Trân Châu', names)

    def test_get_restaurant_dishes_not_found(self):
        res = self.client.get('/api/restaurants/99999/dishes')
        self.assertEqual(res.status_code, 404)

    def test_add_restaurant_dish_api_success(self):
        self.login_as(self.owner)

        res = self.client.post('/restaurant/dish/add', data={
            'name': 'Cà Phê Muối',
            'category_id': str(self.category.id),
            'price': '28000',
            'description': 'Đậm đà béo ngậy',
            'flavor_tags': 'béo, ngọt, đậm'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn('/restaurant/dashboard', res.headers['Location'])

        dish = Dish.query.filter_by(name='Cà Phê Muối', restaurant_id=self.restaurant.id).first()
        self.assertIsNotNone(dish)
        self.assertEqual(int(dish.price), 28000)

    def test_add_restaurant_dish_api_unauthorized_customer(self):
        cust = self.create_user(username='cust_try_add_dish', role=RoleEnum.CUSTOMER)
        self.login_as(cust)

        res = self.client.post('/restaurant/dish/add', data={
            'name': 'Món Lậu',
            'category_id': str(self.category.id),
            'price': '10000'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers['Location'], '/')
