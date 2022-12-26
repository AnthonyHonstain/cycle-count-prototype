from django.contrib import admin
from .models import Location, Product, Inventory, CountSession, IndividualCount, CycleCountModification

admin.site.register(Location)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(CountSession)
admin.site.register(IndividualCount)
admin.site.register(CycleCountModification)
