from test.base import BaseTestCase
from app import dao
from app.models import RoleEnum, OrderStatusEnum


class TestReviewDAO(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='reviewer_user')
        self.owner = self.create_user(username='reviewer_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Bún Bò Xưa')
        self.category = self.create_category(name='Món Nước')
        self.dish1 = self.create_dish(self.restaurant, self.category, name='Bún Bò Đặc Biệt', price=55000)
        self.dish2 = self.create_dish(self.restaurant, self.category, name='Bún Bò Giò Heo', price=45000)

        self.order = self.create_order(
            self.user,
            self.restaurant,
            items=[(self.dish1, 1, 55000)],
            status=OrderStatusEnum.COMPLETED
        )

    def test_save_dish_review_success(self):
        review, err = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=5,
            comment='Rất ngon, nước dùng đậm đà!'
        )

        self.assertIsNone(err)
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Rất ngon, nước dùng đậm đà!')
        self.assertEqual(self.restaurant.rating_avg, 5.0)

    def test_save_dish_review_not_completed_order(self):
        order_pending = self.create_order(
            self.user,
            self.restaurant,
            items=[(self.dish1, 1, 55000)],
            status=OrderStatusEnum.PREPARING
        )

        review, err = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=order_pending.id,
            dish_id=self.dish1.id,
            rating=5
        )
        self.assertIsNone(review)
        self.assertIn("Chỉ có thể đánh giá khi đơn hàng đã giao thành công", err)

    def test_save_dish_review_dish_not_in_order(self):
        review, err = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish2.id,
            rating=5
        )
        self.assertIsNone(review)
        self.assertIn("không thuộc danh sách món", err)

    def test_save_dish_review_invalid_rating(self):
        review_0, err_0 = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=0
        )
        self.assertIsNone(review_0)
        self.assertIn("từ 1 đến 5 sao", err_0)

        review_6, err_6 = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=6
        )
        self.assertIsNone(review_6)
        self.assertIn("từ 1 đến 5 sao", err_6)

    def test_save_dish_review_duplicate_rejected(self):
        dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=5,
            comment='Lần 1'
        )

        dup_review, dup_err = dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=4,
            comment='Lần 2 cố tình gửi lại'
        )
        self.assertIsNone(dup_review)
        self.assertIn("Bạn đã gửi đánh giá cho món ăn này trong đơn hàng rồi", dup_err)

    def test_get_dish_and_restaurant_reviews(self):
        dao.save_or_update_dish_review(
            user_id=self.user.id,
            order_id=self.order.id,
            dish_id=self.dish1.id,
            rating=5,
            comment='Ngon đỉnh cao'
        )

        d_revs = dao.get_dish_reviews(self.dish1.id)
        self.assertEqual(len(d_revs), 1)
        self.assertEqual(d_revs[0].comment, 'Ngon đỉnh cao')

        r_revs = dao.get_restaurant_reviews(self.restaurant.id)
        self.assertEqual(len(r_revs), 1)

        stats = dao.get_restaurant_review_stats(self.restaurant.id)
        self.assertEqual(stats['avg_rating'], 5.0)
        self.assertEqual(stats['total_reviews'], 1)
