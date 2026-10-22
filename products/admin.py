from typing import ClassVar

from django.contrib import admin

from .models import Category, Product, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_accessory', 'created_at')
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {'slug': ('name',)}
    list_filter = ('is_accessory',)



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {'slug': ('name',)}

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'headline', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('headline', 'comment', 'user__username', 'product__name')
