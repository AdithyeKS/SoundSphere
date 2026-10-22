from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_accessory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    APPROVAL_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=10)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='approved')
    rejection_reason = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Technical Specifications
    driver_size = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 40mm Dynamic")
    battery_life = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 30 Hours")
    connectivity = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Bluetooth 5.3")
    noise_cancellation = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. ANC")
    frequency_response = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 20 Hz - 20,000 Hz")
    impedance = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 32 Ohms")
    weight = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 250g")
    warranty = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 1 Year Warranty")

    class Meta:
        db_table = 'products'


    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def average_rating(self):
        if hasattr(self, 'avg_rating') and self.avg_rating is not None:
            return round(self.avg_rating, 1)
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg is not None else 0.0

    @property
    def review_count(self):
        if hasattr(self, 'total_reviews') and self.total_reviews is not None:
            return self.total_reviews
        return self.reviews.count()

    def __str__(self):
        return self.name



class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    headline = models.CharField(max_length=150)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ('-created_at',)
        unique_together = ('product', 'user')

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"
