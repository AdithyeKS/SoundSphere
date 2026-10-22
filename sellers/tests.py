from django.contrib.auth.models import User
from django.test import Client, TestCase

from accounts.models import SellerProfile, UserProfile
from products.models import Category, Product


class SellerApprovalWorkflowTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', email='admin@soundsphere.com', password='password123')
        self.category = Category.objects.create(name='Wireless Headphones', is_accessory=False)

    def test_seller_registration_defaults_to_unapproved(self):
        response = self.client.post('/accounts/register/', {
            'role': 'seller',
            'first_name': 'Boat',
            'last_name': 'Seller',
            'email': 'seller@boat.com',
            'phone': '9876543210',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'store_name': 'Boat Official Store',
            'tax_id': 'GST123456',
            'location': 'Mumbai, India',
            'state': 'Maharashtra',
            'store_description': 'Official Boat Audio Store'
        })
        self.assertEqual(response.status_code, 302)
        
        seller_user = User.objects.get(email='seller@boat.com')
        self.assertTrue(hasattr(seller_user, 'seller_profile'))
        self.assertFalse(seller_user.seller_profile.is_approved)

    def test_unapproved_seller_cannot_add_product(self):
        seller_user = User.objects.create_user(username='pending_seller', email='pending@test.com', password='password123')
        UserProfile.objects.filter(user=seller_user).update(role='seller')
        SellerProfile.objects.create(user=seller_user, store_name='Pending Store', phone='12345', status='pending')

        self.client.login(username='pending_seller', password='password123')
        response = self.client.get('/seller/products/add/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/seller/dashboard/')

    def test_admin_approves_seller_and_allows_product_creation(self):
        seller_user = User.objects.create_user(username='boat_owner', email='boat@test.com', password='password123')
        UserProfile.objects.filter(user=seller_user).update(role='seller')
        seller_profile = SellerProfile.objects.create(user=seller_user, store_name='Boat Audio', phone='12345', status='pending')

        # Admin logs in and approves seller
        self.client.login(username='admin', password='password123')
        approve_res = self.client.get(f'/admin-panel/sellers/approve/{seller_profile.id}/')
        self.assertEqual(approve_res.status_code, 302)

        seller_profile.refresh_from_db()
        self.assertTrue(seller_profile.is_approved)

        # Approved seller logs in and creates product
        self.client.login(username='boat_owner', password='password123')
        add_res = self.client.post('/seller/products/add/', {
            'name': 'Boat Rockerz 550',
            'category': self.category.id,
            'price': '49.99',
            'description': 'Super extra bass headphone',
            'stock': 20,
            'driver_size': '50mm',
            'battery_life': '20 Hours',
            'connectivity': 'Bluetooth 5.0',
            'noise_cancellation': 'Passive'
        })
        self.assertEqual(add_res.status_code, 302)

        # Verify product was created and linked to seller
        product = Product.objects.filter(name='Boat Rockerz 550').first()
        self.assertIsNotNone(product)
        self.assertEqual(product.seller, seller_profile)

    def test_rejection_and_reapply_workflow_with_counts(self):
        # 1. Register a seller
        seller_user = User.objects.create_user(username='sony_audio', email='sony@audio.com', password='password123')
        UserProfile.objects.filter(user=seller_user).update(role='seller')
        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            store_name='Sony Audio Store',
            phone='9876543210',
            tax_id='GST999',
            location='Kochi',
            state='Kerala',
            store_description='Premium Sony noise cancelling wireless audio headphones',
            status='pending',
            reapplication_count=0
        )

        # 2. Admin rejects seller
        self.client.login(username='admin', password='password123')
        reject_res = self.client.post(f'/admin-panel/sellers/reject/{seller_profile.id}/', {
            'rejection_reason': 'GSTIN is invalid. Please provide official authorized dealership certificate.'
        })
        self.assertEqual(reject_res.status_code, 302)

        seller_profile.refresh_from_db()
        self.assertEqual(seller_profile.status, 'rejected')
        self.assertEqual(seller_profile.rejection_reason, 'GSTIN is invalid. Please provide official authorized dealership certificate.')

        # Verify admin moderation page lists rejected seller without Re-approve button
        mod_res = self.client.get('/admin-panel/sellers/moderation/?tab=rejected')
        self.assertEqual(mod_res.status_code, 200)
        self.assertContains(mod_res, 'Sony Audio Store')
        self.assertContains(mod_res, 'GSTIN is invalid')
        self.assertContains(mod_res, 'Attempt #1')
        self.assertContains(mod_res, 'Awaiting Reapply')
        self.assertNotContains(mod_res, 'Re-approve')

        # 3. Rejected seller logs in and views dashboard
        self.client.login(username='sony_audio', password='password123')
        dash_res = self.client.get('/seller/dashboard/')
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, 'Seller Application Not Approved')
        self.assertContains(dash_res, 'GSTIN is invalid')
        self.assertContains(dash_res, 'Edit Brand')
        self.assertContains(dash_res, 'Application Attempt #1')

        # 4. Seller resubmits application via reapply view
        reapply_page_res = self.client.get('/seller/reapply/')
        self.assertEqual(reapply_page_res.status_code, 200)
        self.assertContains(reapply_page_res, 'Brand Reapplication')

        post_res = self.client.post('/seller/reapply/', {
            'store_name': 'Sony Audio Pro Labs',
            'tagline': 'Engineered for Pure Acoustics',
            'store_description': 'Official distributor of studio monitoring headphones and wireless gear.',
            'phone': '9876543210',
            'tax_id': 'GSTVALID12345',
            'location': 'Kochi',
            'state': 'Kerala',
            'reapplication_notes': 'Updated official GSTIN to GSTVALID12345 and added authorized distributor status.',
            'compliance_agreed': 'on'
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertEqual(post_res.url, '/seller/dashboard/')

        seller_profile.refresh_from_db()
        self.assertEqual(seller_profile.status, 'pending')
        self.assertTrue(seller_profile.has_reapplied)
        self.assertEqual(seller_profile.store_name, 'Sony Audio Pro Labs')
        self.assertEqual(seller_profile.reapplication_count, 1)
        self.assertEqual(seller_profile.reapplication_notes, 'Updated official GSTIN to GSTVALID12345 and added authorized distributor status.')
        self.assertIsNotNone(seller_profile.reapplied_at)

        # 5. Verify seller dashboard reflects updated attempt count (#2) and pending status
        updated_dash = self.client.get('/seller/dashboard/')
        self.assertEqual(updated_dash.status_code, 200)
        self.assertContains(updated_dash, 'Seller Reapplication Under Review')
        self.assertContains(updated_dash, 'Attempt #2')

        # 6. Verify admin moderation page now shows reapplied seller with Re-approve button enabled
        self.client.login(username='admin', password='password123')
        admin_mod_pending = self.client.get('/admin-panel/sellers/moderation/')
        self.assertEqual(admin_mod_pending.status_code, 200)
        self.assertContains(admin_mod_pending, 'Sony Audio Pro Labs')
        self.assertContains(admin_mod_pending, 'Reapplied (Attempt #2)')

        admin_mod_rejected = self.client.get('/admin-panel/sellers/moderation/?tab=rejected')
        self.assertEqual(admin_mod_rejected.status_code, 200)
        self.assertContains(admin_mod_rejected, 'Sony Audio Pro Labs')
        self.assertContains(admin_mod_rejected, 'Re-approve')

