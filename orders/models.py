import uuid

from django.contrib.auth.models import User
from django.db import models

from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Confirmed', 'Confirmed'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Refund Initiated', 'Refund Initiated'),
        ('Refunded', 'Refunded'),
    )

    order_number = models.CharField(max_length=50, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Shipping details
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')

    # Pricing details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"SS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.full_name}"

    @property
    def is_cancellable(self):
        return self.status in ['Pending', 'Processing', 'Confirmed', 'Packed', 'Shipped']

    @property
    def estimated_delivery_date(self):
        import datetime
        try:
            days = max([item.estimated_delivery_days for item in self.items.all()] or [3])
        except Exception:
            days = 3
        return self.created_at + datetime.timedelta(days=days)

    @property
    def is_paid_online(self):
        if hasattr(self, 'payment') and self.payment:
            return self.payment.payment_method != 'cod' and self.payment_status in ['Paid', 'Refund Initiated', 'Refunded']
        return self.payment_status in ['Paid', 'Refund Initiated', 'Refunded']

    @property
    def is_cod(self):
        if hasattr(self, 'payment') and self.payment:
            return self.payment.payment_method == 'cod'
        return False

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200) # Snapshot in case product is edited/deleted
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'order_items'
        unique_together = ('order', 'product')

    @property
    def total_price(self):
        return self.price * self.quantity

    @property
    def estimated_delivery_days(self):
        if self.product and self.product.seller and self.order:
            seller_state = self.product.seller.state
            order_state = self.order.state
            if seller_state and order_state and seller_state.strip().lower() == order_state.strip().lower():
                return 1
            return 3
        return 3

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit / Debit Card'),
        ('upi', 'UPI / QR Code'),
        ('netbanking', 'Net Banking'),
        ('cod', 'Cash on Delivery'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='card')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Success')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"
