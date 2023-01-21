import factory
import faker
from factory.django import DjangoModelFactory
from django.utils import timezone

from .models import Location, Product, Inventory


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    description = factory.Faker('ean')


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    description = factory.Faker('sentence')
    sku = factory.Faker('ean')


class InventoryFactory(DjangoModelFactory):
    class Meta:
        model = Inventory

    location = factory.SubFactory(LocationFactory)
    product = factory.SubFactory(ProductFactory)
    qty = factory.Faker('random_int', max=20)
    created_at = factory.Faker('date_time', tzinfo=timezone.timezone.utc)
    updated_at = factory.Faker('date_time', tzinfo=timezone.timezone.utc)
