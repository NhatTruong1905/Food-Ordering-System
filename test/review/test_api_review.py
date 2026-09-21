import json
from test.base import BaseTestCase
from app.models import RoleEnum, OrderStatusEnum


class TestReviewAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='api_reviewer_user')
        self.owner = self.create_user(username='api_reviewer_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Bánh Cuốn Tây Hồ')
        self.category = self.create_category(name='Món Nóng')
        self.dish = self.create_dish(self.restaurant, self.category, name='Bánh Cuốn Nóng', price=35000)

        self.order = self.create_order(
            self.user,
            self.restaurant,
            items=[(self.dish, 1, 35000)],
            status=OrderStatusEnum.COMPLETED
        )

    def test_submit_dish_review_api_success(self):
        self.login_as(self.user)

        res = self.client.post(f'/api/orders/{self.order.id}/reviews',
                               data=json.dumps({
                                   'dish_id': self.dish.id,
                                   'rating': 5,
                                   'comment': 'Nước chấm ngon xuất sắc!'
                               }),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['review']['rating'], 5)

    def test_submit_dish_review_api_unauthenticated(self):
        res = self.client.post(f'/api/orders/{self.order.id}/reviews',
                               data=json.dumps({
                                   'dish_id': self.dish.id,
                                   'rating': 5
                               }),
                               content_type='application/json')
        # Login required redirects or returns unauthorized
        self.assertIn(res.status_code, (302, 401))

    def test_get_dish_reviews_api(self):
        # Submit a review first
        self.login_as(self.user)
        self.client.post(f'/api/orders/{self.order.id}/reviews',
                         data=json.dumps({
                             'dish_id': self.dish.id,
                             'rating': 5,
                             'comment': 'Bánh cuốn rất ngon'
                         }),
                         content_type='application/json')

        res = self.client.get(f'/api/dishes/{self.dish.id}/reviews')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['reviews'][0]['comment'], 'Bánh cuốn rất ngon')

    def test_get_restaurant_reviews_api(self):
        self.login_as(self.user)
        self.client.post(f'/api/orders/{self.order.id}/reviews',
                         data=json.dumps({
                             'dish_id': self.dish.id,
                             'rating': 5,
                             'comment': 'Tuyệt vời'
                         }),
                         content_type='application/json')

        res = self.client.get(f'/api/restaurants/{self.restaurant.id}/reviews')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total_reviews'], 1)
        self.assertEqual(data['rating_avg'], 5.0)
