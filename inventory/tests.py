from django.test import TestCase
from django.urls import reverse

from cyclecount.models import Location, Product, Inventory


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
