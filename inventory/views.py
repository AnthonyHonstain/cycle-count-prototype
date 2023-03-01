import math
import time
import logging
import uuid
from typing import Optional

import requests
from pydantic import BaseModel
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from cyclecount.models import Inventory


class ProductModel(BaseModel):
    id: int
    sku: str
    description: str


class ProductClient:
    def __init__(self):
        # logging.basicConfig(level=logging.DEBUG)
        self.s = requests.Session()
        # Experimenting with an adapter to control retry behavior.
        # s.mount('http://', HTTPAdapter(max_retries=Retry(total=1)))
        self.provenance_id = uuid.uuid1()
        self.headers = {'provenance': str(self.provenance_id)}

    def get_product(self, product_id: int) -> Optional[ProductModel]:
        response = self.s.get(f'http://127.0.0.1:8001/product/products/{product_id}/', headers=self.headers)
        if response.status_code == 200:
            product = ProductModel(**response.json())
            return product
        return None


def list_inventory(request: HttpRequest) -> HttpResponse:
    return render(request, 'inventory/list_inventory.html', {})


'''
WHY:
Why we have two very similar methods in this view:
  * inventory_table_from_db
  * inventory_table_from_product_svc
Both of these should spit out a very similar behavior.

'''
def inventory_table_from_db(request: HttpRequest) -> HttpResponse:

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
        for inv in inventory:
            inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': inv.product.sku, 'qty': inv.qty})

    print(f'DB - found {len(inventory_records)} many records of total:{inventory_count}, ',
          f'slice on start-end:{start}-{end} '
          f'sql_count_perf:{int(pt0.result * 1000)} sql:{int(pt1.result * 1000)}')
    result = {
        'last_page': math.ceil(inventory_count / size),
        'data': inventory_records
    }
    return JsonResponse(result)


def inventory_table_from_product_svc(request: HttpRequest) -> HttpResponse:

    page = int(request.GET.get('page')) - 1
    size = int(request.GET.get('size'))
    print(f'page:{page} size:{size}')

    with PerfTrack() as pt0:
        inventory_count = Inventory.objects.count()

    start = size * page
    end = start + size

    product_client = ProductClient()

    with PerfTrack() as pt1:
        inventory = Inventory.objects.select_related('location').all().order_by('id')[start:end]

        inventory_records = []
        for inv in inventory:
            product_model = product_client.get_product(inv.product_id)

            if product_model:
                inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': product_model.sku, 'qty': inv.qty})
            else:
                inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': None, 'qty': inv.qty})

    print(f'API {str(product_client.provenance_id)} - found {len(inventory_records)} many records of total:{inventory_count}, ',
          f'slice on start-end:{start}-{end} '
          f'sql_count_perf:{int(pt0.result * 1000)}ms API_perf:{int(pt1.result * 1000)}ms')
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
