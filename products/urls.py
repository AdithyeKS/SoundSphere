from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('catalog/', views.product_list_view, name='list'),
    path('product/<slug:slug>/', views.product_detail_view, name='detail'),
    path('product/<slug:slug>/review/', views.add_review_view, name='add_review'),
    path('search-suggestions/', views.search_suggestions_view, name='search_suggestions'),
]
