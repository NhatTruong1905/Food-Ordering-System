from decimal import Decimal
from test.base import BaseTestCase
from app import dao
from app.models import RoleEnum


class TestDishDAO(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user(username='dish_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Bếp Việt')
        self.cat1 = self.create_category(name='Món Nước')
        self.cat2 = self.create_category(name='Món Khô')

    def test_get_all_categories(self):
        cats = dao.get_all_categories()
        self.assertEqual(len(cats), 2)
        names = [c.name for c in cats]
        self.assertIn('Món Nước', names)
        self.assertIn('Món Khô', names)

    def test_add_dish(self):
        new_dish = dao.add_dish(
            restaurant_id=self.restaurant.id,
            category_id=self.cat1.id,
            name='Phở Bò Tái Lăn',
            description='Phở tái lăn đậm đà',
            price=55000,
            image_url='https://example.com/pho.jpg',
            flavor_tags='đậm đà, nóng sốt'
        )

        self.assertIsNotNone(new_dish.id)
        self.assertEqual(new_dish.name, 'Phở Bò Tái Lăn')
        self.assertEqual(new_dish.price, Decimal('55000'))
        self.assertEqual(new_dish.restaurant_id, self.restaurant.id)
        self.assertEqual(new_dish.category_id, self.cat1.id)
        self.assertTrue(new_dish.is_active)

    def test_get_dishes_by_restaurant(self):
        d1 = self.create_dish(self.restaurant, self.cat1, name='Món 1', price=30000, is_active=True)
        d2 = self.create_dish(self.restaurant, self.cat2, name='Món 2', price=40000, is_active=True)
        d3 = self.create_dish(self.restaurant, self.cat1, name='Món Ẩn', price=50000, is_active=False)

        # Another restaurant's dish
        other_owner = self.create_user(username='other_owner', role=RoleEnum.RESTAURANT)
        other_rest = self.create_restaurant(other_owner, name='Quán Khác')
        self.create_dish(other_rest, self.cat1, name='Món Quán Khác', price=60000)

        dishes = dao.get_dishes_by_restaurant(self.restaurant.id)
        self.assertEqual(len(dishes), 2)
        dish_ids = [d.id for d in dishes]
        self.assertIn(d1.id, dish_ids)
        self.assertIn(d2.id, dish_ids)
        self.assertNotIn(d3.id, dish_ids)
