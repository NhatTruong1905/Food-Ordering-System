import json
from test.base import BaseTestCase
from flask import session


class TestCartAPI(BaseTestCase):
    def test_add_to_cart_api(self):
        payload = {
            'restaurant_id': '10',
            'dish_id': '101',
            'name': 'Gà Nướng Muối Ớt',
            'price': 150000
        }
        res = self.client.post('/api/carts',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['stats']['total_quantity'], 1)
        self.assertEqual(data['stats']['total_amount'], 150000)

        # Add second time (increments quantity)
        res2 = self.client.post('/api/carts',
                                data=json.dumps(payload),
                                content_type='application/json')
        data2 = res2.get_json()
        self.assertEqual(data2['stats']['total_quantity'], 2)
        self.assertEqual(data2['stats']['total_amount'], 300000)

    def test_update_cart_api(self):
        # First add an item
        self.client.post('/api/carts',
                         data=json.dumps({'restaurant_id': '10', 'dish_id': '101', 'price': 50000}),
                         content_type='application/json')

        # Update quantity to 5
        res = self.client.put('/api/carts/10/101',
                              data=json.dumps({'quantity': 5}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['item_subtotal'], 250000)
        self.assertEqual(data['grand_total_quantity'], 5)

        # Update quantity to 0 (should remove item)
        res_zero = self.client.put('/api/carts/10/101',
                                   data=json.dumps({'quantity': 0}),
                                   content_type='application/json')
        self.assertEqual(res_zero.status_code, 200)
        data_zero = res_zero.get_json()
        self.assertEqual(data_zero['grand_total_quantity'], 0)

    def test_delete_cart_api(self):
        self.client.post('/api/carts',
                         data=json.dumps({'restaurant_id': '10', 'dish_id': '101', 'price': 50000}),
                         content_type='application/json')

        res = self.client.delete('/api/carts/10/101')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['grand_total_quantity'], 0)

    def test_clear_cart_api(self):
        self.client.post('/api/carts',
                         data=json.dumps({'restaurant_id': '10', 'dish_id': '101', 'price': 50000}),
                         content_type='application/json')

        res = self.client.get('/clear-cart')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Đã xóa sạch giỏ hàng cũ", res.get_data(as_text=True))
