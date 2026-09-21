from test.base import BaseTestCase
from app.models import RoleEnum


class TestAuthAPI(BaseTestCase):
    def test_login_view_get(self):
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)

        user = self.create_user(username='logged_in_user')
        self.login_as(user)
        res_logged = self.client.get('/login')
        self.assertEqual(res_logged.status_code, 302)
        self.assertIn('/', res_logged.headers['Location'])

    def test_login_process_success(self):
        self.create_user(username='john', password='mypassword123')
        res = self.client.post('/login', data={
            'username': 'john',
            'password': 'mypassword123'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers['Location'], '/')

    def test_login_process_invalid_credentials(self):
        self.create_user(username='john', password='mypassword123')
        res = self.client.post('/login', data={
            'username': 'john',
            'password': 'wrongpassword'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_register_view_get(self):
        res = self.client.get('/register')
        self.assertEqual(res.status_code, 200)

    def test_register_process_success(self):
        res = self.client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@gmail.com',
            'phone': '0987111222',
            'address': '123 Đường ABC',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_register_process_mismatched_password(self):
        res = self.client.post('/register', data={
            'username': 'failuser',
            'email': 'failuser@gmail.com',
            'phone': '0987111333',
            'password': 'password123',
            'confirm_password': 'different_password'
        })
        self.assertEqual(res.status_code, 200)

    def test_logout(self):
        user = self.create_user(username='user_logout')
        self.login_as(user)

        res = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_profile_requires_login(self):
        res = self.client.get('/profile', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_profile_update_info(self):
        user = self.create_user(username='profile_user', email='profile@gmail.com', phone='0909000111')
        self.login_as(user)

        res = self.client.post('/profile', data={
            'email': 'updated_profile@gmail.com',
            'phone': '0909000222',
            'address': '789 Updated Address',
            'taste_preferences': 'Thích ăn chay'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn('/profile', res.headers['Location'])
        self.assertEqual(user.email, 'updated_profile@gmail.com')
        self.assertEqual(user.phone, '0909000222')
        self.assertEqual(user.address, '789 Updated Address')
