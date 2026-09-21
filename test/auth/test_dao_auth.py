from test.base import BaseTestCase
from app import dao
from app.models import RoleEnum, User


class TestAuthDAO(BaseTestCase):
    def test_hash_and_verify_password(self):
        raw_pw = 'secret123'
        hashed = dao.hash_password(raw_pw)
        self.assertTrue(dao.verify_password(raw_pw, hashed))
        self.assertFalse(dao.verify_password('wrongpass', hashed))
        self.assertFalse(dao.verify_password('', hashed))

    def test_add_user_and_auth_user_success(self):
        user = dao.add_user(
            username='user1',
            password='mypassword',
            email='user1@example.com',
            phone='0987654321',
            address='123 Duong 1, HCM',
            role=RoleEnum.CUSTOMER
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'user1')

        authenticated = dao.auth_user('user1', 'mypassword')
        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.id, user.id)

    def test_auth_user_failure(self):
        dao.add_user('user2', 'correct_pw', 'user2@example.com')
        self.assertIsNone(dao.auth_user('user2', 'wrong_pw'))
        self.assertIsNone(dao.auth_user('nonexistent_user', 'any_pw'))

    def test_check_user_exists(self):
        dao.add_user('existing_user', 'pw', 'exist@example.com', phone='0911222333')

        err_user = dao.check_user_exists(username='existing_user')
        self.assertEqual(err_user, "Tên đăng nhập đã tồn tại!")

        err_email = dao.check_user_exists(email='exist@example.com')
        self.assertEqual(err_email, "Email này đã được sử dụng!")

        err_phone = dao.check_user_exists(phone='0911222333')
        self.assertEqual(err_phone, "Số điện thoại này đã được sử dụng!")

        self.assertIsNone(dao.check_user_exists(username='fresh_user', email='fresh@example.com', phone='0999999999'))

    def test_check_user_update_conflicts(self):
        u1 = self.create_user(username='u1', email='u1@example.com', phone='0901000001')
        u2 = self.create_user(username='u2', email='u2@example.com', phone='0902000002')

        err_self = dao.check_user_update_conflicts(u1.id, email='u1@example.com', phone='0901000001')
        self.assertIsNone(err_self)

        err_email = dao.check_user_update_conflicts(u1.id, email='u2@example.com')
        self.assertEqual(err_email, "Email này đã được sử dụng bởi tài khoản khác!")

        err_phone = dao.check_user_update_conflicts(u1.id, phone='0902000002')
        self.assertEqual(err_phone, "Số điện thoại này đã được sử dụng bởi tài khoản khác!")

    def test_update_user_profile(self):
        user = self.create_user(username='update_me', password='old_password', email='old@example.com')

        updated, err = dao.update_user_profile(
            user_id=user.id,
            email='new@example.com',
            phone='0988776655',
            address='456 New Road',
            taste_preferences='Cay, ngọt',
            new_password='new_secure_pw'
        )

        self.assertIsNone(err)
        self.assertEqual(updated.email, 'new@example.com')
        self.assertEqual(updated.phone, '0988776655')
        self.assertEqual(updated.address, '456 New Road')
        self.assertEqual(updated.taste_preferences, 'Cay, ngọt')
        self.assertTrue(dao.verify_password('new_secure_pw', updated.password_hash))

    def test_get_user_by_id(self):
        user = self.create_user(username='user_by_id')
        fetched = dao.get_user_by_id(user.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, user.id)

        self.assertIsNone(dao.get_user_by_id(999999))
