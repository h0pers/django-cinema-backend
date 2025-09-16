from django.contrib import admin

from .models import Transaction


class TransactionInline(admin.TabularInline):
    model = Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ["external_payment_id"]
