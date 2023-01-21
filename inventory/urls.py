from django.urls import path

from . import views

app_name = 'inventory'
urlpatterns = [
    path('list_inventory/', views.list_inventory, name='list_inventory'),
    path('inventory_table/', views.inventory_table, name='inventory_table'),
]