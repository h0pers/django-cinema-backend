from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.api.cinema.seasons.models import Season
from apps.api.cinema.titles.models import Title
from apps.api.cinema.videos.models import ToggleWatchModel, Video
from apps.core.models import DescriptiveModel, OrderableModel


class EpisodeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            season__title__status=Title.Status.PUBLISHED,
        )


class Episode(OrderableModel, ToggleWatchModel, DescriptiveModel):
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name='episodes',
    )
    poster = models.ImageField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    video = models.OneToOneField(
        Video,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='as_episode',
    )

    objects = models.Manager()
    public = EpisodeManager()

    class Meta(OrderableModel.Meta, ToggleWatchModel.Meta, DescriptiveModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["ordering", "season"],
                name='unique_episode_ordering',
            ),
        ]
        permissions = (
            # Use this permission as per object assigned
            ("can_watch_episode", _("Watch episode")),
        )

    def clean(self):
        if (
            self.video is not None
            and self.video.Role != Video.Role.EPISODE
        ):
            raise ValidationError(_("The video is not episode"))

        super().clean()
