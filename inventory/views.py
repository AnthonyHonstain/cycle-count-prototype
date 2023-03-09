import math
import time
import structlog
import uuid
from typing import Optional

import requests
from pydantic import BaseModel
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from cyclecount.models import Inventory


log = structlog.get_logger(__name__)


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
        self.headers = {'X-Correlation-ID': str(self.provenance_id)}

    def get_product(self, product_id: int) -> Optional[ProductModel]:
        log.info('get_product', product_id=product_id, correlation_id=str(self.provenance_id))
        # Todo - in order to play nice with the X-Request-ID in the logging framework
        #  should I set a request header so retries are clearer ?
        #  https://django-structlog.readthedocs.io/en/latest/events.html#django-s-requestmiddleware
        response = self.s.get(f'http://127.0.0.1:8001/product/products/{product_id}/', headers=self.headers)
        if response.status_code == 200:
            product = ProductModel(**response.json())
            return product
        return None


def list_inventory(request: HttpRequest) -> HttpResponse:
    return render(request, 'inventory/list_inventory.html', {})


'''
Explanation on why we have inventory_table_from_db and inventory_table_from_product_svc

WHY: They are being using to experiment with pagination, and to experiment with extracting
logic to a new microservice.  

Both of these should general equivalent results for calls made by the list_inventory view.

inventory_table_from_product_svc looks pretty unusual, but it is being used to experiment
with the requests library (experimenting with sessions, logging, and error handling).
The large number of small requests to the product service isn't the way I would solve
the problem of list_inventory + pagination, but its a vehicle for experimentation.
'''


def inventory_table_from_db(request: HttpRequest) -> HttpResponse:

    page = int(request.GET.get('page')) - 1
    size = int(request.GET.get('size'))
    log.info('pagination_details', page=page, size=size)

    with PerfTrack() as pt0:
        inventory_count = Inventory.objects.count()

    start = size * page
    end = start + size

    with PerfTrack() as pt1:
        inventory = Inventory.objects.select_related('product', 'location').all().order_by('id')[start:end]

        inventory_records = []
        for inv in inventory:
            inventory_records.append({'id': inv.id, 'location': inv.location.description, 'sku': inv.product.sku, 'qty': inv.qty})

    log.info('inventory DB results', returned_count=len(inventory_records), total_count=inventory_count, slice=f'{start}-{end}', sql_count_perf_ms=int(pt0.result * 1000), sql_perf_ms=int(pt1.result * 1000))
    result = {
        'last_page': math.ceil(inventory_count / size),
        'data': inventory_records
    }
    return JsonResponse(result)


def inventory_table_from_product_svc(request: HttpRequest) -> HttpResponse:

    page = int(request.GET.get('page')) - 1
    size = int(request.GET.get('size'))
    log.info('pagination_details', page=page, size=size)

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

    log.info('inventory API results', returned_count=len(inventory_records), total_count=inventory_count, slice=f'{start}-{end}', sql_count_perf_ms=int(pt0.result * 1000), API_perf_ms=int(pt1.result * 1000))
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
