from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/', views.payment_gateway_view, name='payment'),
    path('process-payment/', views.process_payment_view, name='process_payment'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='confirmation'),
    path('my-orders/', views.order_history_view, name='my_orders'),
    path('detail/<str:order_number>/', views.order_detail_view, name='detail'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel'),
    path('invoice/<str:order_number>/', views.download_invoice_view, name='invoice'),
]
