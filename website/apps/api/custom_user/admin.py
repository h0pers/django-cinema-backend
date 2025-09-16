from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group as DjangoGroup
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.core.models import PaymentProviderType

from .models import CustomGroup, UserSubscription
from .services.user_subscription_service import UserSubscriptionService

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    ordering = []
    list_display = ("email", "first_name", "last_name", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Payments"), {"fields": ("stripe_customer_id",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


class CustomGroupAdmin(GroupAdmin):
    pass


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    readonly_fields = ["external_payment_id"]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change and obj.payment_provider == PaymentProviderType.STRIPE:
            if "disabled" in form.changed_data:
                if obj.disabled:
                    UserSubscriptionService.disable(obj)

            elif "canceled" in form.changed_data:
                if obj.canceled:
                    UserSubscriptionService.cancel(obj)

        super().save_model(request, obj, form, change)



admin.site.unregister(DjangoGroup)
admin.site.register(User, CustomUserAdmin)
admin.site.register(CustomGroup, CustomGroupAdmin)
