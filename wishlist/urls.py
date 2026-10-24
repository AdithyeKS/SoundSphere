from django.urls import path

from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_view, name='view'),
    path('toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle'),
    path('move-to-cart/<int:product_id>/', views.move_to_cart_view, name='move_to_cart'),
    path('move-all-to-cart/', views.move_all_to_cart_view, name='move_all_to_cart'),
    path('clear/', views.clear_wishlist_view, name='clear'),
]
