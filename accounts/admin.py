from django.contrib import admin

from .models import CustomerFeedback, ShippingAddress, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'postal_code', 'is_default')
    list_filter = ('is_default', 'state', 'country')
    search_fields = ('full_name', 'street_address', 'city', 'postal_code')

@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category', 'subject', 'rating', 'created_at')
    list_filter = ('category', 'rating', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
