from test.base import BaseTestCase
from app import dao
from app.models import RoleEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum


class TestOrderDAO(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='order_user')
        self.owner = self.create_user(username='order_owner', role=RoleEnum.RESTAURANT)
        self.restaurant = self.create_restaurant(self.owner, name='Cơm Tấm Cali')
        self.category = self.create_category(name='Cơm')
        self.dish = self.create_dish(self.restaurant, self.category, name='Sườn Chả', price=40000)

    def test_get_orders_by_user(self):
        # Create two cash orders (one PENDING, one COMPLETED)
        o1 = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING, payment_method=PaymentMethodEnum.CASH)
        o2 = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.COMPLETED, payment_method=PaymentMethodEnum.CASH)

        # Unpaid VNPAY order should NOT appear in customer order list
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                          payment_method=PaymentMethodEnum.VNPAY, payment_status=PaymentStatusEnum.PENDING)

        orders_all = dao.get_orders_by_user(self.user.id, status='ALL')
        self.assertEqual(len(orders_all), 2)

        orders_pending = dao.get_orders_by_user(self.user.id, status='PENDING')
        self.assertEqual(len(orders_pending), 1)
        self.assertEqual(orders_pending[0].id, o1.id)

        orders_completed = dao.get_orders_by_user(self.user.id, status='COMPLETED')
        self.assertEqual(len(orders_completed), 1)
        self.assertEqual(orders_completed[0].id, o2.id)

    def test_get_order_status_counts(self):
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING, payment_method=PaymentMethodEnum.CASH)
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.CONFIRMED, payment_method=PaymentMethodEnum.CASH)
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.DELIVERING, payment_method=PaymentMethodEnum.CASH)
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.COMPLETED, payment_method=PaymentMethodEnum.CASH)

        counts = dao.get_order_status_counts(self.user.id)
        self.assertEqual(counts['ALL'], 4)
        self.assertEqual(counts['PENDING'], 1)
        self.assertEqual(counts['PREPARING'], 1)  # CONFIRMED maps to PREPARING
        self.assertEqual(counts['DELIVERING'], 1)
        self.assertEqual(counts['COMPLETED'], 1)

    def test_cancel_order_success(self):
        order = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                                  payment_method=PaymentMethodEnum.CASH, payment_status=PaymentStatusEnum.PENDING)
        success, msg = dao.cancel_order(order.id, self.user.id)
        self.assertTrue(success)
        self.assertEqual(order.status, OrderStatusEnum.CANCELLED)

    def test_cancel_order_not_allowed(self):
        # Order already preparing
        o_prep = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PREPARING,
                                   payment_method=PaymentMethodEnum.CASH, payment_status=PaymentStatusEnum.PENDING)
        success, msg = dao.cancel_order(o_prep.id, self.user.id)
        self.assertFalse(success)
        self.assertIn("Chỉ có thể hủy", msg)

        # Order already paid
        o_paid = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.PENDING,
                                   payment_method=PaymentMethodEnum.VNPAY, payment_status=PaymentStatusEnum.SUCCESS)
        success_paid, msg_paid = dao.cancel_order(o_paid.id, self.user.id)
        self.assertFalse(success_paid)
        self.assertIn("đã được thanh toán", msg_paid)

    def test_get_active_order_for_user(self):
        self.create_order(self.user, self.restaurant, status=OrderStatusEnum.COMPLETED, payment_method=PaymentMethodEnum.CASH)
        active_o = self.create_order(self.user, self.restaurant, status=OrderStatusEnum.DELIVERING, payment_method=PaymentMethodEnum.CASH)

        found = dao.get_active_order_for_user(self.user.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, active_o.id)
