import random
from django.core.management.base import BaseCommand

from cyclecount.factories import LocationFactory, ProductFactory, InventoryFactory


class Command(BaseCommand):
    help = 'Generate test data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating new data...")

        # First make the products we can pick from.
        products = []
        for _ in range(200000):
            products.append(ProductFactory())

        for _ in range(100000):
            location = LocationFactory()
            inventory_fks = set()
            for _ in range(0, random.randint(0, 4)):
                inventory_fks.add(random.choice(products))

            for product in inventory_fks:
                InventoryFactory(product=product, location=location)
