from django.urls import path

from . import views

app_name = 'inventory'
urlpatterns = [
    path('list-inventory/', views.list_inventory, name='list_inventory'),
    path('inventory-table_db/', views.inventory_table_from_db, name='inventory_table_db'),
    path('inventory-table-api/', views.inventory_table_from_product_svc, name='inventory_table_api'),
]