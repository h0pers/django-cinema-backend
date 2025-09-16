from django.contrib import admin

from apps.api.payments.transactions.admin import TransactionInline

from .models import Order, OrderItem


class OrderItemInline(admin.StackedInline):
    fields = [
        "product",
        "quantity",
        "total_price",
    ]
    readonly_fields = ["total_price"]
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = [
        "total_price",
        "created_at",
    ]
    inlines = [
        OrderItemInline,
        TransactionInline,
    ]

    def change_view(self, request, object_id, *args, **kwargs):
        kwargs["extra_context"] = {
            "stripe_payment": True,
        }
        return super().change_view(request, object_id, *args, **kwargs)
