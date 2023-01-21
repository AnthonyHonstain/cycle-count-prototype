import math
import time

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from cyclecount.models import Inventory


def list_inventory(request: HttpRequest) -> HttpResponse:
    return render(request, 'inventory/list_inventory.html', {})


def inventory_table(request: HttpRequest) -> HttpResponse:

    page = int(request.GET.get('page')) - 1
    size = int(request.GET.get('size'))
    print(f'page:{page} size:{size}')

    with PerfTrack() as pt0:
        inventory_count = Inventory.objects.count()

    start = size * page
    end = start + size

    with PerfTrack() as pt1:
        inventory = Inventory.objects.select_related('product', 'location').all().order_by('id')[start:end]

        inventory_records = []
        for inv in inventory:  # [start:end]:
            inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': inv.product.sku, 'qty': inv.qty})

    print(f'found {len(inventory_records)} many records of total:{inventory_count},',
          f' slice on start-end:{start}-{end} sql_count_perf:{pt0.result * 1000} sql:{pt1.result * 1000}')
    result = {
        'last_page': math.ceil(inventory_count / size),
        'data': inventory_records
    }
    return JsonResponse(result)


class PerfTrack:
    def __enter__(self):
        self.time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.result = time.perf_counter() - self.time
