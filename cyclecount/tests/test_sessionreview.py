from django.test import TestCase
from django.test import Client
from django.urls import reverse

from cyclecount.models import CustomUser, CountSession, Location, Product, IndividualCount, Inventory, \
    CycleCountModification


class SessionReviewTests(TestCase):
    USERNAME = 'cycle_count_test'
    PASSWORD = 'test-pw'
    user = None
    location_00_empty = None
    location_01 = None
    location_02 = None
    product_01 = None
    product_02 = None

    count_session_empty = None
    count_session = None
    individual_count_01 = None
    logged_in_client: Client = None

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(cls.USERNAME, 'cc@test.com', cls.PASSWORD)

        cls.location_00_empty = Location(description='test-location-00-empty-desc')
        cls.location_00_empty.save()
        cls.location_01 = Location(description='test-location-01-desc')
        cls.location_01.save()
        cls.location_02 = Location(description='test-location-02-desc')
        cls.location_02.save()
        # TODO - probably going to have to expand to account for:
        #     empty (no row in DB), empty (row but 0 qty),
        #     existing qty > cc qty, existing qty < cc qty,
        #     existing qty == cc qty
        # TODO - also expand to cover a count_session that has counts in two different locations, since that
        #   has an impact on the logic in the session_review view.

        cls.product_01 = Product(description='test-product-01', sku='test-sku-01')
        cls.product_01.save()
        cls.product_02 = Product(description='test-product-02', sku='test-sku-02')
        cls.product_02.save()

        cls.count_session_empty = CountSession(created_by=cls.user)
        cls.count_session_empty.save()

        cls.count_session = CountSession(created_by=cls.user)
        cls.count_session.save()
        cls.individual_count_01 = IndividualCount(
            associate=cls.user, session=cls.count_session, location=cls.location_01, product=cls.product_01,
            state=IndividualCount.CountState.ACTIVE
        )
        cls.individual_count_01.save()
        cls.logged_in_client = Client()
        cls.logged_in_client.login(username=cls.USERNAME, password=cls.PASSWORD)

    def test_no_auth(self):
        response = self.client.get(reverse('cyclecount:list_active_sessions'))
        self.assertRedirects(response, '/accounts/login/?next=/cycle-count/list-active-sessions/', status_code=302)

        response = self.client.get(reverse('cyclecount:session_review', args=(self.count_session_empty.id,)))
        self.assertRedirects(response, f'/accounts/login/?next=/cycle-count/session-review/{self.count_session_empty.id}', status_code=302)

        response = self.client.get(reverse('cyclecount:finalize_session', args=(self.count_session_empty.id,)))
        self.assertRedirects(response, f'/accounts/login/?next=/cycle-count/finalize-session/{self.count_session_empty.id}', status_code=302)

    def test_begin_cycle_count_loads_and_has_link_to_start(self):
        url = reverse('cyclecount:list_active_sessions')
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:session_review', args=(self.count_session_empty.id,)))

    def test_session_review_empty_session(self):
        url = reverse('cyclecount:session_review', args=(self.count_session_empty.id,))
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)
        # There isn't much to show here because the session didn't have any counts.
        # TODO - maybe we want to force the user into canceling a session with no counts
        self.assertContains(response, reverse('cyclecount:finalize_session', args=(self.count_session_empty.id,)))

    def test_session_review(self):
        url = reverse('cyclecount:session_review', args=(self.count_session.id,))
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:finalize_session', args=(self.count_session.id,)))

        location_quantities = response.context['location_quantities']
        self.assertEqual(
            location_quantities[(self.location_01.id, self.product_01.id)],
            {
                'location': self.location_01,
                'product': self.product_01,
                'cyclecount_qty': 1,
                'qty': 0
            }
        )
        # self.assert???(response.content.decode(), 'cycle_count_test test-location-00-empty-desc test-sku-01 1 Active')

    def test_session_review_with_unusual_cyclecount_qty(self):
        # This is a somewhat unusual case, as we currently don't have a way to generate individual count records
        # with a quantity greater than 1, but the column allow for it, so adding some basic checks.
        self.individual_count_01.qty = 2
        self.individual_count_01.save()

        url = reverse('cyclecount:session_review', args=(self.count_session.id,))
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cyclecount:finalize_session', args=(self.count_session.id,)))

        location_quantities = response.context['location_quantities']
        self.assertEqual(
            location_quantities[(self.location_01.id, self.product_01.id)],
            {
                'location': self.location_01,
                'product': self.product_01,
                'cyclecount_qty': 2,
                'qty': 0
            }
        )

    def finalize_session_helper(self, final_state: CountSession.FinalState) -> None:
        """
        Call finalize_session, assert redirect happens, assert CountSession record is updated
        :param final_state:
        :return:
        """
        url = reverse('cyclecount:finalize_session', args=(self.count_session.id,))
        response = self.logged_in_client.post(url, {'choice': final_state})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cyclecount:list_active_sessions'))
        updated_count_session = CountSession.objects.get(pk=self.count_session.id)
        self.assertEqual(final_state, updated_count_session.final_state)
        return

    def test_session_review_already_finalized(self):
        self.finalize_session_helper(CountSession.FinalState.ACCEPTED)

        url = reverse('cyclecount:session_review', args=(self.count_session.id,))
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('cyclecount:finalize_session', args=(self.count_session.id,)))

        count_session = response.context['count_session']
        self.assertEqual(CountSession.FinalState.ACCEPTED, count_session.final_state)

    def test_session_review_multiple_locations(self):
        Inventory(location=self.location_02, product=self.product_01, qty=3).save()  # This shouldn't have any impact
        Inventory(location=self.location_02, product=self.product_02, qty=5).save()
        individual_count_02 = IndividualCount(
            associate=self.user, session=self.count_session, location=self.location_02, product=self.product_02,
            state=IndividualCount.CountState.ACTIVE
        )
        individual_count_02.save()

        url = reverse('cyclecount:session_review', args=(self.count_session.id,))
        response = self.logged_in_client.get(url)
        self.assertEqual(response.status_code, 200)

        location_quantities = response.context['location_quantities']
        self.assertDictEqual(location_quantities, {
            (self.location_01.id, self.product_01.id): {
                'location': self.location_01,
                'product': self.product_01,
                'cyclecount_qty': 1,
                'qty': 0,
            },
            (self.location_02.id, self.product_02.id): {
                'location': self.location_02,
                'product': self.product_02,
                'cyclecount_qty': 1,
                'qty': 5,
            },
        })

    def test_finalize_session_canceled_creates_inventory_record(self):
        self.finalize_session_helper(CountSession.FinalState.CANCELED)

        new_inventory_record = Inventory.objects.filter(location=self.location_01, product=self.product_01).first()
        self.assertIsNone(new_inventory_record)

        cc_mod = CycleCountModification.objects.filter(
            session=self.count_session, location=self.location_01, product=self.product_01
        ).first()
        self.assertIsNone(cc_mod)

    def test_finalize_session_accepted_creates_inventory_record(self):
        # Key component of this test is checking the CREATION of an Inventory record (location,product)
        inventory_record = Inventory.objects.filter(location=self.location_01, product=self.product_01).first()
        self.assertIsNone(inventory_record)  # Sanity check nothing exists before doing the test.

        self.finalize_session_helper(CountSession.FinalState.ACCEPTED)

        self.check_inventory_and_ccmod(self.location_01, self.product_01, 0, 1)

    def test_finalize_session_accepted_updates_inventory_record(self):
        # Key component of this test is checking the UPDATE of an Inventory record (location,product)
        Inventory(location=self.location_01, product=self.product_01, qty=5).save()

        self.finalize_session_helper(CountSession.FinalState.ACCEPTED)

        self.check_inventory_and_ccmod(self.location_01, self.product_01, 5, 1)

    def test_finalize_session_accepted_creates_and_update(self):
        Inventory(location=self.location_01, product=self.product_01, qty=5).save()
        individual_count_02 = IndividualCount(
            associate=self.user, session=self.count_session, location=self.location_02, product=self.product_02,
            state=IndividualCount.CountState.ACTIVE
        )
        individual_count_02.save()

        self.finalize_session_helper(CountSession.FinalState.ACCEPTED)

        self.check_inventory_and_ccmod(self.location_01, self.product_01, 5, 1)
        self.check_inventory_and_ccmod(self.location_02, self.product_02, 0, 1)

    def check_inventory_and_ccmod(self, location: Location, product: Product, old_qty: int, new_qty: int) -> None:
        inventory_record_02 = Inventory.objects.filter(location=location, product=product).first()
        self.assertEqual(1, inventory_record_02.qty)
        cc_mod = CycleCountModification.objects.filter(
            session=self.count_session, location=location, product=product
        ).first()
        self.assertEqual(old_qty, cc_mod.old_qty)
        self.assertEqual(new_qty, cc_mod.new_qty)

    def test_finalize_session_thats_already_finalized(self):
        self.finalize_session_helper(CountSession.FinalState.ACCEPTED)

        url = reverse('cyclecount:finalize_session', args=(self.count_session.id,))
        # Linchpin of the test - we re-run it again on an already finalized CountSession
        with self.assertRaises(Exception):
            self.logged_in_client.post(url, {'choice': CountSession.FinalState.ACCEPTED})

