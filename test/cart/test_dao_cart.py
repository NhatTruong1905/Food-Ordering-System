from test.base import BaseTestCase
from app.utils import get_cart_stats, get_res_total


class TestCartDAO(BaseTestCase):
    def test_get_cart_stats_empty(self):
        stats = get_cart_stats({})
        self.assertEqual(stats['total_quantity'], 0)
        self.assertEqual(stats['total_amount'], 0)

    def test_get_cart_stats_with_items(self):
        cart = {
            '1': {
                'restaurant_id': '1',
                'items': {
                    '10': {'name': 'Phở', 'price': 50000, 'quantity': 2},
                    '11': {'name': 'Quẩy', 'price': 5000, 'quantity': 4}
                }
            },
            '2': {
                'restaurant_id': '2',
                'items': {
                    '20': {'name': 'Trà đá', 'price': 3000, 'quantity': 3}
                }
            }
        }
        stats = get_cart_stats(cart)
        self.assertEqual(stats['total_quantity'], 9)
        self.assertEqual(stats['total_amount'], 129000)

    def test_get_res_total(self):
        cart = {
            '1': {
                'restaurant_id': '1',
                'items': {
                    '10': {'name': 'Phở', 'price': 50000, 'quantity': 2},
                    '11': {'name': 'Quẩy', 'price': 5000, 'quantity': 4}
                }
            }
        }
        self.assertEqual(get_res_total(cart, '1'), 120000)
        self.assertEqual(get_res_total(cart, '999'), 0)
