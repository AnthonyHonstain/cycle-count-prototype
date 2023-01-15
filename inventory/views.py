from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from cyclecount.models import Inventory


def list_inventory(request: HttpRequest) -> HttpResponse:
    inventory = Inventory.objects.select_related('product', 'location').all()
    inventory_records = []
    for inv in inventory:
        inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': inv.product.sku, 'qty': inv.qty})
    return render(request, 'inventory/list_inventory.html', {'inventory_records': inventory_records})
