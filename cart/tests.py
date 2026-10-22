from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from cart.models import Cart, CartItem
from products.models import Category, Product


class CartTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name="Wireless Headphones")
        self.product = Product.objects.create(
            name="Test Headphones",
            category=self.category,
            price=Decimal("100.00"),
            stock=10
        )

    def test_cart_totals(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal("200.00"))
        self.assertEqual(cart.shipping, Decimal("0.00")) # Free over $150
        self.assertEqual(cart.tax, Decimal("16.00"))
        self.assertEqual(cart.grand_total, Decimal("216.00"))

    def test_staff_cannot_add_to_cart(self):
        User.objects.create_user(username='adminstaff', password='password123', is_staff=True)
        self.client.login(username='adminstaff', password='password123')
        response = self.client.post(f'/cart/add/{self.product.id}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("Admin Viewer Mode", data['message'])
