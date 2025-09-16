from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


class UniqueNamedModel(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='%(class)s_unique_name'
            )
        ]

    def __str__(self):
        return self.name


class DescriptiveModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True
        indexes = [
            GinIndex(
                fields=['name'],
                opclasses=['gin_trgm_ops'],
                name='%(class)s_trgm_search_idx',
            ),
            GinIndex(
                SearchVector("name", config="simple"),
                SearchVector("description", config="simple"),
                name="%(class)s_gin_search_idx",
            )
        ]

    def __str__(self):
        return self.name


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        abstract = True


class OrderableModel(models.Model):
    ordering = models.PositiveIntegerField(
        help_text=_("Element ordering number"),
        validators=[
            MinValueValidator(1),
        ],
        db_index=True,
    )

    class Meta:
        abstract = True
        get_latest_by = "ordering"
        ordering = ["ordering"]
