import requests
from django.test import TestCase
from django.urls import reverse

from .views import ProductClient
from cyclecount.models import Location, Product, Inventory
from typing import cast
from unittest.mock import patch, call


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_request_get(product_id: int) -> requests.Response:
    product_response_01 = {"id": 1, "description": "test-product-01", "sku": "test-sku-01"}
    if product_id == 1:
        return cast(requests.Response, MockResponse(product_response_01, 200))
    return cast(requests.Response, MockResponse(None, 404))


class InventoryTests(TestCase):
    location_00_empty = None
    location_01 = None
    location_02 = None
    product_01 = None
    product_02 = None

    count_session_empty = None
    count_session = None
    individual_count_01 = None

    @classmethod
    def setUpTestData(cls):
        cls.location_00_empty = Location(description='test-location-00-empty-desc')
        cls.location_00_empty.save()
        cls.location_01 = Location(description='test-location-01-desc')
        cls.location_01.save()
        cls.location_02 = Location(description='test-location-02-desc')
        cls.location_02.save()

        cls.product_01 = Product(description='test-product-01', sku='test-sku-01')
        cls.product_01.save()
        cls.product_02 = Product(description='test-product-02', sku='test-sku-02')
        cls.product_02.save()

    def test_list_inventory(self):
        url = reverse('inventory:list_inventory')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_inventory_table_empty(self):
        url = reverse('inventory:inventory_table_db')
        response = self.client.get(url, {'page': 1, 'size': 10})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"last_page": 0, "data": []})

    def test_inventory_table_single(self):
        inv01 = Inventory(location=self.location_01, product=self.product_01, qty=5)
        inv01.save()

        url = reverse('inventory:inventory_table_db')
        response = self.client.get(url, {'page': 1, 'size': 10})
        self.assertEqual(response.status_code, 200)
        expected_result = {"last_page": 1, "data": [
            {'id': inv01.id, 'location': inv01.location.description, 'sku': inv01.product.sku, 'qty': inv01.qty}
        ]}
        self.assertJSONEqual(response.content, expected_result)

    def test_inventory_table_single_API(self):
        inv01 = Inventory(location=self.location_01, product=self.product_01, qty=5)
        inv01.save()

        product_response = {"id": 1, "description": "test-product-01", "sku": "test-sku-01"}
        with patch.object(ProductClient, 'get_product', return_value=MockResponse(product_response, 200)) as mock_method:
            url = reverse('inventory:inventory_table_api')
            response = self.client.get(url, {'page': 1, 'size': 10})

        mock_method.assert_called_once_with(1)
        self.assertEqual(response.status_code, 200)
        expected_result = {"last_page": 1, "data": [
            {'id': inv01.id, 'location': inv01.location.description, 'sku': inv01.product.sku, 'qty': inv01.qty},
        ]}
        self.assertJSONEqual(response.content, expected_result)

    def test_inventory_table_two_records_API(self):
        inv01 = Inventory(location=self.location_01, product=self.product_01, qty=5)
        inv01.save()
        inv02 = Inventory(location=self.location_02, product=self.product_02, qty=1)
        inv02.save()

        with patch('inventory.views.ProductClient.get_product', side_effect=mocked_request_get) as mock_method:
            url = reverse('inventory:inventory_table_api')
            response = self.client.get(url, {'page': 1, 'size': 10})

        mock_method.assert_has_calls([call(1), call(2)])
        self.assertEqual(response.status_code, 200)
        expected_result = {"last_page": 1, "data": [
            {'id': inv01.id, 'location': inv01.location.description, 'sku': inv01.product.sku, 'qty': inv01.qty},
            {'id': inv02.id, 'location': inv02.location.description, 'sku': None, 'qty': inv02.qty},
        ]}
        self.assertJSONEqual(response.content, expected_result)