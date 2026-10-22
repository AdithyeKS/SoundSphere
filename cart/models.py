from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_id = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum((item.total_price for item in self.items.all()), Decimal('0.00'))

    @property
    def tax(self):
        return round(self.subtotal * Decimal('0.08'), 2)

    @property
    def shipping(self):
        if self.subtotal == Decimal('0.00'):
            return Decimal('0.00')
        return Decimal('0.00') if self.subtotal >= Decimal('150.00') else Decimal('15.00')

    @property
    def grand_total(self):
        return self.subtotal + self.tax + self.shipping

    def __str__(self):
        return f"Cart ({self.user.username if self.user else self.session_id})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')

    @property
    def total_price(self):
        return self.product.current_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


