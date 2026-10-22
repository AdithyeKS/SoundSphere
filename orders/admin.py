from django.contrib import admin

from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

class PaymentInline(admin.StackedInline):
    model = Payment
    can_delete = False
    readonly_fields = ('transaction_id', 'payment_method', 'amount', 'status', 'created_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'email', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone')
    inlines = (OrderItemInline, PaymentInline)
