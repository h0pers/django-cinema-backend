from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.api.cinema.episodes.filters import EpisodeFilterSet
from apps.api.cinema.episodes.models import Episode
from apps.api.cinema.episodes.v1.serializers import EpisodeSerializer
from apps.api.cinema.seasons.filters import SeasonFilterSet
from apps.api.cinema.seasons.models import Season
from apps.api.cinema.seasons.v1.serializers import SeasonSerializer
from apps.api.cinema.videos.mixins import TogglWatchViewSetMixin
from apps.api.mixins import VersioningAPIViewMixin

from .filters import TitleCrewMemberFilterSet, TitleFilterSet
from .models import Title
from .v1.serializers import (
    TitleCrewMember,
    TitleCrewMemberSerializer,
    TitleSerializer,
)


class TitleViewSet(
    VersioningAPIViewMixin,
    TogglWatchViewSetMixin,
    ModelViewSet,
):
    queryset = Title.objects.all()
    filterset_class = TitleFilterSet
    version_map = {
        "v1": {
            "serializer_class": TitleSerializer,
        }
    }

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        season_number = self.kwargs.get("season_number")

        user = getattr(self.request, "user", None)
        public_only = not (user and user.is_authenticated and user.is_staff)

        def base_qs(model):
            return model.public.all() if public_only else model.objects.all()

        if self.action in {"list", "retrieve"}:
            return base_qs(Title)

        if self.action == "crew_list":
            return TitleCrewMember.objects.filter(title=pk)

        if self.action in {"seasons_list", "seasons_retrieve"}:
            return base_qs(Season).filter(title=pk)

        if self.action in {"episodes_list", "episodes_retrieve"}:
            filters = {"season__title": pk}
            if season_number is not None:
                filters["season__ordering"] = season_number
            return base_qs(Episode).filter(**filters)

        return super().get_queryset()

    @action(
        methods=['GET'],
        detail=True,
        url_path="crew",
        filterset_class=TitleCrewMemberFilterSet,
        version_map={
            "v1": {
                "serializer_class": TitleCrewMemberSerializer,
            }
        }
    )
    def crew_list(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=True,
        url_path="seasons",
        filterset_class=SeasonFilterSet,
        version_map={
            "v1": {
                "serializer_class": SeasonSerializer,
            }
        }
    )
    def seasons_list(self, request, pk, *args, **kwargs):
        title = get_object_or_404(Title, pk=pk)

        if not title.is_show:
            raise ValidationError({"type": _("Title is not show type")})

        return self.list(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=True,
        lookup_field = "ordering",
        lookup_url_kwarg = "season_number",
        url_path="seasons/(?P<season_number>[^/.]+)",
        filterset_class=None,
        version_map={
            "v1": {
                "serializer_class": SeasonSerializer,
            }
        }
    )
    def seasons_retrieve(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(Title, pk=pk)

        if not obj.is_show:
            raise ValidationError({"type": _("Title is not show type")})

        return self.retrieve(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=True,
        url_path="seasons/(?P<season_number>[^/.]+)/episodes",
        filterset_class=EpisodeFilterSet,
        version_map={
            "v1": {
                "serializer_class": EpisodeSerializer,
            }
        }
    )
    def episodes_list(self, request, pk, season_number, *args, **kwargs):
        title = get_object_or_404(Title, pk=pk)

        if not title.is_show:
            raise ValidationError({"type": _("Title is not show type")})

        get_object_or_404(Season, title=title, ordering=season_number)

        return self.list(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=True,
        lookup_field="ordering",
        lookup_url_kwarg="episode_number",
        url_path="seasons/(?P<season_number>[^/.]+)/episodes/(?P<episode_number>[^/.]+)",
        filterset_class=None,
        version_map={
            "v1": {
                "serializer_class": EpisodeSerializer,
            }
        }
    )
    def episodes_retrieve(self, request, pk, season_number, *args, **kwargs):
        title = get_object_or_404(Title, pk=pk)

        if not title.is_show:
            raise ValidationError({"type": _("Title is not show type")})

        get_object_or_404(Season, title=title, ordering=season_number)
        return self.retrieve(request, *args, **kwargs)


class TitleCrewViewSet(
    VersioningAPIViewMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = TitleCrewMember.objects.all()
    version_map = {
        "v1": {
            "serializer_class": TitleCrewMemberSerializer,
        }
    }
