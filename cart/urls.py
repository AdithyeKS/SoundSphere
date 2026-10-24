from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='detail'),
    path('add/<int:product_id>/', views.cart_add_view, name='add'),
    path('buy-now/<int:product_id>/', views.buy_now_view, name='buy_now'),
    path('update/<int:item_id>/', views.cart_update_view, name='update'),
    path('remove/<int:item_id>/', views.cart_remove_view, name='remove'),
    path('coupon/apply/', views.apply_coupon_view, name='apply_coupon'),
]
