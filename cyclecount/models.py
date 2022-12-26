from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class Location(models.Model):
    description = models.CharField(max_length=200)


class Product(models.Model):
    description = models.CharField(max_length=200)
    sku = models.CharField(max_length=200)


class Inventory(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CountSession(models.Model):
    associate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class IndividualCount(models.Model):
    session = models.ForeignKey(CountSession, on_delete=models.CASCADE)
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    associate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.TextChoices('Active', 'Deleted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CycleCountModification(models.Model):
    # TODO - still not sure how I want to model the final approval of counts that triggers the finally inventory count
    session = models.ForeignKey(CountSession, on_delete=models.CASCADE)
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    associate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# https://learndjango.com/tutorials/django-best-practices-referencing-user-model
# https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#auth-custom-user
class CustomUser(AbstractUser):
    pass

