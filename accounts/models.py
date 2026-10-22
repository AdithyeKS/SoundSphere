from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    @property
    def is_seller(self):
        return self.role == 'seller' or hasattr(self.user, 'seller_profile')

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"

class SellerProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    
    # Store & Brand Details
    store_name = models.CharField(max_length=150, unique=True, verbose_name="Brand Name")
    tagline = models.CharField(max_length=200, blank=True, null=True, verbose_name="Brand Tagline")
    store_description = models.TextField(blank=True, null=True, verbose_name="Brand Description")
    phone = models.CharField(max_length=20)
    
    # Business & Location Details
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Business ID / Tax ID")
    location = models.CharField(max_length=150, blank=True, null=True, verbose_name="Store Location (City/District)")
    state = models.CharField(max_length=100, default='Kerala', verbose_name="State")
    logo = models.ImageField(upload_to='seller_logos/', blank=True, null=True, verbose_name="Brand Logo")
    
    # Approval Status & Admin Feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    reapplication_notes = models.TextField(blank=True, null=True, verbose_name="Reapplication Notes")
    reapplication_count = models.PositiveIntegerField(default=0, verbose_name="Reapplication Count")
    reapplied_at = models.DateTimeField(blank=True, null=True, verbose_name="Reapplied At")
    has_reapplied = models.BooleanField(default=False, verbose_name="Has Reapplied")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seller_profiles'

    @property
    def is_approved(self):
        return self.status == 'approved'

    def __str__(self):
        return f"Brand: {self.store_name} ({self.status.title()})"

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shipping_addresses'

    def save(self, *args, **kwargs):
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.postal_code}"

class CustomerFeedback(models.Model):
    CATEGORY_CHOICES = (
        ('general', 'General Inquiry'),
        ('product', 'Product & Technical Spec Question'),
        ('order', 'Order & Delivery Issue'),
        ('website', 'Website Feedback / Suggestion'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_feedbacks'
        ordering = ('-created_at',)

    def __str__(self):
        return f"Feedback from {self.name} ({self.subject})"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

