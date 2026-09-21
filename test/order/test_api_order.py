import json
from test.base import BaseTestCase
from app.models import RoleEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum, Order


class TestOrderAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='api_order_user')
        self.owner = self.create_user(username='api_order_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Bún Đậu Mắm Tôm')
        self.category = self.create_category(name='Món Chính')
        self.dish = self.create_dish(self.restaurant, self.category, name='Bún Đậu Thập Cẩm', price=65000)

    def test_checkout_cash_success(self):
        self.login_as(self.user)

        with self.client.session_transaction() as sess:
            sess['cart'] = {
                str(self.restaurant.id): {
                    'restaurant_id': str(self.restaurant.id),
                    'items': {
                        str(self.dish.id): {
                            'id': str(self.dish.id),
                            'name': self.dish.name,
                            'price': float(self.dish.price),
                            'quantity': 2
                        }
                    }
                }
            }

        res = self.client.post(f'/api/checkout/{self.restaurant.id}',
                               data=json.dumps({
                                   'delivery_address': '123 Đường Số 1, Quận 1',
                                   'payment_method': 'CASH'
                               }),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['payment_method'], 'CASH')

        order = Order.query.get(data['order_id'])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, OrderStatusEnum.PENDING)
        self.assertEqual(int(order.total_amount), 130000)
        self.assertEqual(order.payment.method, PaymentMethodEnum.CASH)

    def test_checkout_vnpay_cancels_old_unpaid(self):
        self.login_as(self.user)

        old_order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                                      payment_method=PaymentMethodEnum.VNPAY, payment_status=PaymentStatusEnum.PENDING)

        with self.client.session_transaction() as sess:
            sess['cart'] = {
                str(self.restaurant.id): {
                    'restaurant_id': str(self.restaurant.id),
                    'items': {
                        str(self.dish.id): {
                            'id': str(self.dish.id),
                            'name': self.dish.name,
                            'price': float(self.dish.price),
                            'quantity': 1
                        }
                    }
                }
            }

        res = self.client.post(f'/api/checkout/{self.restaurant.id}',
                               data=json.dumps({
                                   'delivery_address': '456 Lê Lợi, Quận 1',
                                   'payment_method': 'VNPAY'
                               }),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['payment_method'], 'VNPAY')
        self.assertIn('payment_url', data)

        self.assertEqual(old_order.status, OrderStatusEnum.CANCELLED)

    def test_cancel_order_api(self):
        order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                                  payment_method=PaymentMethodEnum.CASH)
        self.login_as(self.user)

        res = self.client.post(f'/api/orders/{order.id}/cancel')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(order.status, OrderStatusEnum.CANCELLED)

    def test_update_order_status_api(self):
        order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING)
        self.login_as(self.owner)

        res = self.client.put(f'/api/orders/{order.id}/status',
                              data=json.dumps({'status': 'PREPARING'}),
                              content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(order.status, OrderStatusEnum.PREPARING)

    def test_update_order_status_unauthorized_restaurant(self):
        order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING)

        other_owner = self.create_user(username='other_rest_owner', role=RoleEnum.RESTAURANT)
        self.login_as(other_owner)

        res = self.client.put(f'/api/orders/{order.id}/status',
                              data=json.dumps({'status': 'PREPARING'}),
                              content_type='application/json')

        self.assertEqual(res.status_code, 403)

    def test_pay_vnpay_test_api(self):
        order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                                  payment_method=PaymentMethodEnum.VNPAY, payment_status=PaymentStatusEnum.PENDING)
        self.login_as(self.user)

        res = self.client.post(f'/api/orders/{order.id}/pay_vnpay_test',
                               data=json.dumps({
                                   'card_number': '9704198526191432198',
                                   'card_holder': 'NGUYEN VAN A',
                                   'issue_date': '07/15',
                                   'otp': '123456'
                               }),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(order.payment.status, PaymentStatusEnum.SUCCESS)
