from django.test import TestCase
from django.urls import reverse

from cyclecount.models import CustomUser, CountSession, Location, Product, IndividualCount


class CycleCountTests(TestCase):
    USERNAME = 'cycle_count_test'
    PASSWORD = 'test-pw'
    user = None
    location = None
    product = None
    session = None

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(cls.USERNAME, 'cc@test.com', cls.PASSWORD)
        cls.location = Location(description='test-location-desc')
        cls.location.save()
        cls.product = Product(description='test-product-01', sku='test-sku-01')
        cls.product.save()
        cls.session = CountSession(created_by=cls.user)
        cls.session.save()

    def test_begin_cycle_count_loads_and_has_link_to_start(self):
        url = reverse('cyclecount:begin_cycle_count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:start_new_session'))

    def test_start_session(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:start_new_session')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        counts = CountSession.objects.filter(created_by=self.user).count()
        self.assertEqual(counts, 2, 'New CountSession was created')

    def test_start_session_without_auth(self):
        url = reverse('cyclecount:start_new_session')
        with self.assertRaises(ValueError):
            self.client.post(url)

    def test_scan_prompt_location(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:scan_prompt_location', args=(self.session.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:scan_location', args=(self.session.id,)))

    def test_scan_location(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:scan_location', args=(self.session.id,))
        response = self.client.post(url, {'location-barcode': self.location.description})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         reverse('cyclecount:scan_prompt_product', args=(self.session.id, self.location.id)))

    def test_scan_prompt_product(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:scan_prompt_product', args=(self.session.id, self.location.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:scan_product', args=(self.session.id, self.location.id)))

    def test_scan_product(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:scan_product', args=(self.session.id, self.location.id))
        response = self.client.post(url, {'sku': self.product.sku})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         reverse('cyclecount:scan_prompt_product', args=(self.session.id, self.location.id)))

        new_counts = IndividualCount.objects.filter(session=self.session, associate=self.user).count()
        self.assertEqual(new_counts, 1, 'New IndividualCount was created')
