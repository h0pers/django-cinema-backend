from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ["final_price", "is_subscription"]
    prepopulated_fields = {"slug": ["name"]}
    # search_fields = ["sku", "name"]
    # autocomplete_fields = ["variants"]
