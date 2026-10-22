from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import SellerProfile
from products.models import Category, Product


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller1", password="password123")
        self.seller = SellerProfile.objects.create(user=self.user, store_name="SoundSphere Audio", phone="1234567890", status="approved")
        self.category = Category.objects.create(name="Noise-Cancelling Headphones", is_accessory=False)
        self.product = Product.objects.create(
            name="SoundSphere Apex ANC",
            category=self.category,
            seller=self.seller,
            price=Decimal("349.99"),
            discount_price=Decimal("299.99"),
            description="High fidelity noise-cancelling headphones.",
            stock=15,
            driver_size="45mm Custom Beryllium",
            battery_life="40 Hours"
        )

    def test_product_pricing_and_discount(self):
        self.assertTrue(self.product.is_on_sale)
        self.assertEqual(self.product.current_price, Decimal("299.99"))
        self.assertEqual(self.product.discount_percentage, 14)

    def test_product_specifications(self):
        self.assertEqual(self.product.driver_size, "45mm Custom Beryllium")
        self.assertEqual(self.product.battery_life, "40 Hours")

    def test_catalog_view(self):
        response = self.client.get('/catalog/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SoundSphere Apex ANC")
