from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('products/', views.manage_products_view, name='products'),
    path('products/add/', views.add_product_view, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product_view, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product_view, name='delete_product'),
    path('products/toggle-block/<int:product_id>/', views.toggle_product_block_view, name='toggle_product_block'),
    path('orders/', views.manage_orders_view, name='orders'),
    path('orders/update/<str:order_number>/', views.update_order_status_view, name='update_order_status'),
    path('products/moderation/', views.product_moderation_view, name='moderation'),
    path('products/approve/<int:product_id>/', views.approve_product_view, name='approve_product'),
    path('products/reject/<int:product_id>/', views.reject_product_view, name='reject_product'),
    path('sellers/', views.seller_moderation_view, name='sellers'),
    path('sellers/moderation/', views.seller_moderation_view, name='seller_moderation'),
    path('sellers/approve/<int:seller_id>/', views.approve_seller_view, name='approve_seller'),
    path('sellers/reject/<int:seller_id>/', views.reject_seller_view, name='reject_seller'),
    path('users/', views.manage_users_view, name='users'),
    path('users/toggle-active/<int:user_id>/', views.toggle_user_active_view, name='toggle_user_active'),
    path('users/delete/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('feedback/', views.feedback_moderation_view, name='feedback_moderation'),
    path('feedback/delete/<int:feedback_id>/', views.delete_feedback_view, name='delete_feedback'),
    path('reports/', views.analytics_reports_view, name='reports'),
    path('reports/export/csv/', views.export_orders_csv_view, name='export_orders_csv'),
]

