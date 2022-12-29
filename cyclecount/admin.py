from django.contrib import admin
from .models import Location, Product, Inventory, CountSession, IndividualCount, CycleCountModification


class CountSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'count_of_individual_counts')


class IndividualCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'associate_id', 'location_id', 'product_id', 'qty', 'state')


admin.site.register(Location)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(CountSession, CountSessionAdmin)
admin.site.register(IndividualCount, IndividualCountAdmin)
admin.site.register(CycleCountModification)
