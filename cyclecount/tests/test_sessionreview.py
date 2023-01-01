from django.test import TestCase
from django.urls import reverse

from cyclecount.models import CustomUser, CountSession, Location, Product, IndividualCount, Inventory, \
    CycleCountModification


class SessionReviewTests(TestCase):
    USERNAME = 'cycle_count_test'
    PASSWORD = 'test-pw'
    user = None
    location_00_empty = None
    location_01 = None
    product = None
    count_session_empty = None
    count_session = None
    individual_count_01 = None

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(cls.USERNAME, 'cc@test.com', cls.PASSWORD)

        cls.location_00_empty = Location(description='test-location-00-empty-desc')
        cls.location_00_empty.save()
        cls.location_01 = Location(description='test-location-01-desc')
        cls.location_01.save()
        # TODO - probably going to have to expand to account for:
        #     empty (no row in DB), empty (row but 0 qty),
        #     existing qty > cc qty, existing qty < cc qty,
        #     existing qty == cc qty
        # TODO - also expand to cover a count_session that has counts in two different locations, since that
        #   has an impact on the logic in the session_review view.

        cls.product = Product(description='test-product-01', sku='test-sku-01')
        cls.product.save()

        cls.count_session_empty = CountSession(created_by=cls.user)
        cls.count_session_empty.save()

        cls.count_session = CountSession(created_by=cls.user)
        cls.count_session.save()
        cls.individual_count_01 = IndividualCount(
            associate=cls.user, session=cls.count_session, location=cls.location_01, product=cls.product,
            state=IndividualCount.CountState.ACTIVE
        )
        cls.individual_count_01.save()

    def test_begin_cycle_count_loads_and_has_link_to_start(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:list_active_sessions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:session_review', args=(self.count_session_empty.id,)))

    def test_session_review_empty_session(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:session_review', args=(self.count_session_empty.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # There isn't much to show here because the session didn't have any counts.
        # TODO - maybe we want to force the user into canceling a session with no counts
        self.assertContains(response, reverse('cyclecount:finalize_session', args=(self.count_session_empty.id,)))

    def test_session_review_(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:session_review', args=(self.count_session.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:finalize_session', args=(self.count_session.id,)))

        location_quantities = response.context['location_quantities']
        self.assertTrue((self.location_01, self.product) in location_quantities)
        self.assertEqual(
            location_quantities[(self.location_01, self.product)],
            {
                'location': self.location_01,
                'product': self.product,
                'ccQty': 1,
                'qty': 0
            }
        )
        # self.assert???(response.content.decode(), 'cycle_count_test test-location-00-empty-desc test-sku-01 1 Active')

    def test_finalize_session_creates_inventory_record(self):
        # Key component of this test is checking the CREATION of an Inventory record (location,product)
        inventory_record = Inventory.objects.filter(location=self.location_01, product=self.product).first()
        self.assertIsNone(inventory_record)  # Sanity check nothing exists before doing the test.

        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:finalize_session', args=(self.count_session.id,))
        response = self.client.post(url, {'choice': CountSession.FinalState.ACCEPTED})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cyclecount:list_active_sessions'))
        updated_count_session = CountSession.objects.get(pk=self.count_session.id)
        self.assertEqual(CountSession.FinalState.ACCEPTED, updated_count_session.final_state)

        new_inventory_record = Inventory.objects.filter(location=self.location_01, product=self.product).first()
        self.assertEqual(1, new_inventory_record.qty)

        cc_mod = CycleCountModification.objects.filter(session=self.count_session, location_id=self.location_01).first()
        self.assertEqual(self.location_01, cc_mod.location_id)
        self.assertEqual(self.count_session, cc_mod.session)
        self.assertEqual(self.user, cc_mod.associate)

    def test_finalize_session_updates_inventory_record(self):
        # Key component of this test is checking the UPDATE of an Inventory record (location,product)
        Inventory(location=self.location_01, product=self.product, qty=5).save()

        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        url = reverse('cyclecount:finalize_session', args=(self.count_session.id,))
        response = self.client.post(url, {'choice': CountSession.FinalState.ACCEPTED})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cyclecount:list_active_sessions'))
        updated_count_session = CountSession.objects.get(pk=self.count_session.id)
        self.assertEqual(CountSession.FinalState.ACCEPTED, updated_count_session.final_state)

        inventory_record = Inventory.objects.filter(location=self.location_01, product=self.product).first()
        self.assertEqual(1, inventory_record.qty)

        cc_mod = CycleCountModification.objects.filter(session=self.count_session, location_id=self.location_01).first()
        self.assertEqual(self.location_01, cc_mod.location_id)
        self.assertEqual(self.count_session, cc_mod.session)
        self.assertEqual(self.user, cc_mod.associate)
