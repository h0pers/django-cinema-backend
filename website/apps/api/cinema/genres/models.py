from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UniqueNamedModel


class Genre(UniqueNamedModel):
    slug = models.SlugField(max_length=100, unique=True)

    class Meta(UniqueNamedModel.Meta):
        permissions = (
            # Use this permission as per object assigned
            ("can_watch_genre", _("Watch all titles in genre")),
            # General
            ("can_watch_genre_movies", _("Watch all movies in genre")),
            ("can_watch_genre_shows", _("Watch all shows in genre")),
        )
