
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models
from django.db.models import Case, Q, QuerySet, Value, When
from django.db.models.manager import BaseManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import PaymentProviderModel

# Create your models here.

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["stripe_customer_id"],
                condition=~Q(stripe_customer_id=''),
                name="unique_stripe_customer_id",
            )
        ]

    def __str__(self):
        return self.email

    @property
    def stripe_customer(self) -> bool:
        return bool(self.stripe_customer_id)


class CustomGroup(Group):
    class Meta:
        verbose_name = _("group")
        verbose_name_plural = _("groups")
        proxy = True


class UserSubscriptionQuerySet(QuerySet):
    def _active_query(self) -> Q:
        return Q(disabled=False) & (Q(expires__isnull=True) | Q(expires__gte=timezone.now()))

    def active(self):
        return self.filter(self._active_query())

    def with_active_flag(self):
        return self.annotate(
            active=Case(
                When(self._active_query(), then=Value('active')),
                default=Value(False),
                output_field=models.BooleanField()
            )
        )


class UserSubscriptionManager(BaseManager.from_queryset(UserSubscriptionQuerySet)):
    pass


class UserSubscription(PaymentProviderModel):
    order = models.ForeignKey(
        "payments.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    subscription = models.ForeignKey(
        "payments.Subscription",
        on_delete=models.PROTECT,
        related_name='subscribers',
    )
    # Null means infinity subscription
    expires = models.DateTimeField(null=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)

    # Use this field to cancel subscription billing
    # Subscription will be active until the expiration date and don't charged next time
    canceled = models.BooleanField(default=False, editable=False)
    canceled_at = models.DateTimeField(null=True, editable=False)

    # Use this field to disable user subscription immediately
    # Should be used by admins or API to ban user subscription,
    # Use canceled to disable billing
    disabled = models.BooleanField(default=False, editable=False)
    disabled_at = models.DateTimeField(null=True, editable=False)

    objects = UserSubscriptionManager()

    class Meta(PaymentProviderModel.Meta):
        ordering = ["-subscribed_at"]

    def __str__(self):
        return _("%(user)s subscribed to %(subscription)s") % {
            "user": str(self.user),
            "subscription": str(self.subscription),
        }

    @property
    def active(self) -> bool:
        return not self.disabled and (self.expires is None or self.expires >= timezone.now())
