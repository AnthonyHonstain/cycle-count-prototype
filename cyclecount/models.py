from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class Location(models.Model):
    description = models.CharField(max_length=200)


class Product(models.Model):
    description = models.CharField(max_length=200)
    sku = models.CharField(max_length=200)


class Inventory(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CountSession(models.Model):
    class FinalState(models.TextChoices):
        ACCEPTED = 'Accepted'
        CANCELED = 'Canceled'

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_by')

    # Setting the final_state as null initially, not Django convention but what I expect when I query DB
    # https://docs.djangoproject.com/en/4.1/ref/models/fields/#null
    final_state = models.CharField(max_length=10, choices=FinalState.choices, null=True)
    final_state_datetime = models.DateTimeField(null=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='completed_by')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def count_of_individual_counts(self) -> int:
        return IndividualCount.objects.filter(session=self).count()


class IndividualCount(models.Model):
    class CountState(models.TextChoices):
        ACTIVE = 'Active'
        DELETED = 'Deleted'

    associate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(CountSession, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)
    state = models.CharField(max_length=10, choices=CountState.choices, default=CountState.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CycleCountModification(models.Model):
    # TODO - still not sure how I want to model the final approval of counts that triggers the finally inventory count
    session = models.ForeignKey(CountSession, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    old_qty = models.IntegerField()
    new_qty = models.IntegerField()
    associate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# https://learndjango.com/tutorials/django-best-practices-referencing-user-model
# https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#auth-custom-user
class CustomUser(AbstractUser):
    pass

