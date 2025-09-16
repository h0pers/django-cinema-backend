
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.api.cinema.crew.models import CrewMember
from apps.api.cinema.genres.models import Genre
from apps.api.cinema.videos.models import ToggleWatchModel, Video
from apps.core.models import DescriptiveModel, Language


class TitleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Title.Status.PUBLISHED)


class Title(ToggleWatchModel, DescriptiveModel):
    class Status(models.TextChoices):
        # Published means accessible on the website, but not saying it has video files to watch
        PUBLISHED = 'published', _('Published')
        # Hidden from customers, but editable for staff
        DRAFT = 'draft', _('Draft')

    class TitleType(models.TextChoices):
        MOVIE = 'movie', _('Movie')
        SHOW = 'show', _('Show')

    # SEO optimized field, slug is not unique, use this field with the primary key
    # E.g. <int:pk>/<slug:slug>/
    slug = models.SlugField(max_length=255)
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PUBLISHED)
    type = models.CharField(choices=TitleType.choices, max_length=20)
    # Use this field when the date of release is not known
    release_year = models.PositiveSmallIntegerField(null=True, blank=True, help_text=_("UTC Timezone"))
    release_date = models.DateTimeField(null=True, blank=True, help_text=_("UTC Timezone"))
    poster = models.ImageField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    trailer = models.OneToOneField(
        Video,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='as_trailer',
    )
    video = models.OneToOneField(
        Video,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='as_movie',
    )

    objects = models.Manager()
    public = TitleManager()

    class Meta(ToggleWatchModel.Meta, DescriptiveModel.Meta):
        permissions = (
            # Use this permission as per object assigned
            ("can_watch_title", _("Can watch title")),
            # General
            ("can_watch_all", _("Can watch all titles")),
            ("can_watch_all_movies", _("Can watch all movies")),
            ("can_watch_all_shows", _("Can watch all shows")),
        )

    def clean(self):
        if (
            self.release_date is not None and
            self.release_year != self.release_date.year
        ):
            raise ValidationError(_("Release year is not the same as in release date"))

        if (
            self.video is not None and
            not self.is_movie
        ):
            raise ValidationError(_("Video can not be assigned to a non movie title"))

        if (
            self.video is not None and
            self.video.role != Video.Role.MOVIE
        ):
            raise ValidationError(_("Video is not of movie type"))

        if (
            self.trailer is not None and
            self.trailer.role != Video.Role.TRAILER
        ):
            raise ValidationError(_("Video is not of trailer type"))

        super().clean()

    def save(self, *args, **kwargs):
        if (
            self.release_date is not None
        ):
            self.release_year = self.release_date.year
        super().save(*args, **kwargs)

    @property
    def published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def draft(self) -> bool:
        return self.status == self.Status.DRAFT

    @property
    def is_movie(self) -> bool:
        return self.type == self.TitleType.MOVIE

    @property
    def is_show(self) -> bool:
        return self.type == self.TitleType.SHOW


class TitleCrewMember(models.Model):
    class Position(models.TextChoices):
        ACTOR = "actor", _("Actor")
        DIRECTOR = "director", _("Director")
        WRITER = "writer", _("Writer")
        PRODUCER = "producer", _("Producer")
        CINEMATOGRAPHER = "cinematographer", _("Cinematographer")
        EDITOR = "editor", _("Editor")
        COMPOSER = "composer", _("Composer")
        PRODUCTION_DESIGNER = "production_designer", _("Production Designer")
        COSTUME_DESIGNER = "costume_designer", _("Costume Designer")
        MAKEUP_ARTIST = "makeup_artist", _("Makeup Artist")
        SOUND_DESIGNER = "sound_designer", _("Sound Designer")
        VISUAL_EFFECTS = "visual_effects", _("Visual Effects")
        STUNT_COORDINATOR = "stunt_coordinator", _("Stunt Coordinator")
        OTHER = "other", _("Other")

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='crew_members'
    )
    crew_member = models.ForeignKey(
        CrewMember,
        on_delete=models.PROTECT,
        related_name='titles'
    )
    position = models.CharField(
        choices=Position.choices,
        default=Position.OTHER,
        max_length=50,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'crew_member', 'position'],
                name='unique_title_crew_member_position',
                violation_error_message=_("Crew member position must be unique")
            )
        ]

    def __str__(self):
        return str(self.crew_member)
