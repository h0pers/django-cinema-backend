from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.api.cinema.titles.models import Title
from apps.api.cinema.videos.models import ToggleWatchModel
from apps.core.models import DescriptiveModel, OrderableModel


class SeasonManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            title__status=Title.Status.PUBLISHED,
        )


class Season(OrderableModel, ToggleWatchModel, DescriptiveModel):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='seasons',
    )

    objects = models.Manager()
    public = SeasonManager()

    class Meta(OrderableModel.Meta, ToggleWatchModel.Meta, DescriptiveModel.Meta):
        permissions = (
            # Use this permission as per object assigned
            ("can_watch_season", _("Can watch season")),
        )
        constraints = [
            models.UniqueConstraint(
                fields=["title", "ordering"],
                name="unique_title_ordering",
            )
        ]

