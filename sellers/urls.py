from django.urls import path

from . import views

app_name = 'sellers'

urlpatterns = [
    path('register/', views.seller_register_view, name='register'),
    path('login/', views.seller_login_view, name='login'),
    path('dashboard/', views.seller_dashboard_view, name='dashboard'),
    path('reapply/', views.seller_reapply_view, name='reapply'),
    path('products/', views.seller_products_view, name='products'),
    path('products/add/', views.seller_add_product_view, name='add_product'),
    path('products/edit/<int:product_id>/', views.seller_edit_product_view, name='edit_product'),
    path('products/delete/<int:product_id>/', views.seller_delete_product_view, name='delete_product'),
    path('orders/', views.seller_orders_view, name='orders'),
    path('orders/update/<str:order_number>/', views.update_seller_order_status_view, name='update_order_status'),
]
