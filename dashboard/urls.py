from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('products/', views.dashboard_products, name='products'),
    path('customers/', views.dashboard_customers, name='customers'),
]
