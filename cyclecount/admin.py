from django.contrib import admin
from .models import Location, Product, Inventory, CountSession, IndividualCount, CycleCountModification, CustomUser


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'sku')


class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'qty', 'location', 'product')


class CountSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'final_state', 'count_of_individual_counts')


class IndividualCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'associate_id', 'location_id', 'product_id', 'qty', 'state')


admin.site.register(CustomUser)
admin.site.register(Location, LocationAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(CountSession, CountSessionAdmin)
admin.site.register(IndividualCount, IndividualCountAdmin)
admin.site.register(CycleCountModification)
