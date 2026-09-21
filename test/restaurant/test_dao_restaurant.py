from test.base import BaseTestCase
from app import dao, db
from app.models import RoleEnum, Review, OrderStatusEnum


class TestRestaurantDAO(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user(username='rest_owner', role=RoleEnum.RESTAURANT)

    def test_get_restaurant_all(self):
        self.create_restaurant(self.owner, name='Phở Thìn', address='Hà Nội')
        self.create_restaurant(self.owner, name='Bún Bò Huế', address='Huế')

        res_list, total, pages = dao.get_restaurant()
        self.assertEqual(total, 2)
        self.assertEqual(len(res_list), 2)
        self.assertEqual(pages, 1)

    def test_get_restaurant_search_name_and_address(self):
        r1 = self.create_restaurant(self.owner, name='Pizza Ý Hoàng Gia', address='Quận 1, HCM')
        r2 = self.create_restaurant(self.owner, name='Burger King', address='Quận 7, HCM')
        r3 = self.create_restaurant(self.owner, name='Phở 24', address='Đống Đa, Hà Nội')

        by_name, total_name, _ = dao.get_restaurant(name='Pizza')
        self.assertEqual(total_name, 1)
        self.assertEqual(by_name[0].name, r1.name)

        by_addr, total_addr, _ = dao.get_restaurant(address='Hà Nội')
        self.assertEqual(total_addr, 1)
        self.assertEqual(by_addr[0].name, r3.name)

        by_both, total_both, _ = dao.get_restaurant(name='Pizza', address='Quận 1')
        self.assertEqual(total_both, 1)

    def test_get_restaurant_pagination(self):
        for i in range(10):
            self.create_restaurant(self.owner, name=f'Quán {i}', address=f'Địa chỉ {i}')

        page1, total, total_pages = dao.get_restaurant(page=1, page_size=4)
        self.assertEqual(total, 10)
        self.assertEqual(len(page1), 4)
        self.assertEqual(total_pages, 3)

        page3, _, _ = dao.get_restaurant(page=3, page_size=4)
        self.assertEqual(len(page3), 2)

    def test_get_restaurant_by_id(self):
        r_active = self.create_restaurant(self.owner, name='Active Shop', is_active=True)
        r_inactive = self.create_restaurant(self.owner, name='Closed Shop', is_active=False)

        found = dao.get_restaurant_by_id(r_active.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, r_active.id)

        not_found_inactive = dao.get_restaurant_by_id(r_inactive.id)
        self.assertIsNone(not_found_inactive)

        not_found_random = dao.get_restaurant_by_id(99999)
        self.assertIsNone(not_found_random)

    def test_update_restaurant_rating(self):
        cat = self.create_category()
        rest = self.create_restaurant(self.owner, name='Quán Chè')
        dish = self.create_dish(rest, cat, name='Chè Thái')
        user = self.create_user(username='customer1')
        order = self.create_order(user, rest, status=OrderStatusEnum.COMPLETED)

        r1 = Review(user_id=user.id, order_id=order.id, dish_id=dish.id, rating=4, comment='Ngon')
        db.session.add(r1)
        db.session.commit()

        dao.update_restaurant_rating(rest.id)
        self.assertEqual(rest.rating_avg, 4.0)

        user2 = self.create_user(username='customer2')
        order2 = self.create_order(user2, rest, status=OrderStatusEnum.COMPLETED)
        r2 = Review(user_id=user2.id, order_id=order2.id, dish_id=dish.id, rating=5, comment='Rất ngon')
        db.session.add(r2)
        db.session.commit()

        dao.update_restaurant_rating(rest.id)
        self.assertEqual(rest.rating_avg, 4.5)
