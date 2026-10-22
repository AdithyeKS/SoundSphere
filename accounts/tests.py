from django.contrib.auth.models import User
from django.test import Client, TestCase

from accounts.models import SellerProfile, UserProfile


class RoleBasedLoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a customer user
        self.customer = User.objects.create_user(
            username='customer_user',
            email='customer@example.com',
            password='CustomerPassword123!'
        )
        self.customer_profile, _ = UserProfile.objects.get_or_create(user=self.customer)
        self.customer_profile.role = 'customer'
        self.customer_profile.save()

        # Create a seller user
        self.seller = User.objects.create_user(
            username='seller_user',
            email='seller@example.com',
            password='SellerPassword123!'
        )
        self.seller_profile_user, _ = UserProfile.objects.get_or_create(user=self.seller)
        self.seller_profile_user.role = 'seller'
        self.seller_profile_user.save()
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller,
            store_name='Awesome Audio Store',
            phone='9876543210',
            status='approved'
        )

    def test_customer_cannot_login_through_seller_tab(self):
        response = self.client.post('/accounts/login/', {
            'role': 'seller',
            'username': 'customer@example.com',
            'password': 'CustomerPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted. This account is registered as a Customer.")
        # Verify user is NOT authenticated in the session
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_customer_cannot_login_through_seller_login_view(self):
        response = self.client.post('/seller/login/', {
            'username': 'customer@example.com',
            'password': 'CustomerPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted. This account is registered as a Customer.")
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_seller_cannot_login_through_customer_tab(self):
        response = self.client.post('/accounts/login/', {
            'role': 'customer',
            'username': 'seller@example.com',
            'password': 'SellerPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted. This account is registered as a Seller.")
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_customer_can_login_through_customer_tab(self):
        response = self.client.post('/accounts/login/', {
            'role': 'customer',
            'username': 'customer@example.com',
            'password': 'CustomerPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.customer.id)

    def test_seller_can_login_through_seller_tab(self):
        response = self.client.post('/accounts/login/', {
            'role': 'seller',
            'username': 'seller@example.com',
            'password': 'SellerPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/seller/dashboard/')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.seller.id)
