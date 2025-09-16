from functools import partial

from django.db import transaction
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from apps.api.cinema.audio_tracks.filters import AudioTrackFilter
from apps.api.cinema.audio_tracks.models import AudioTrack
from apps.api.cinema.audio_tracks.v1.serializers import AudioTrackSerializer
from apps.api.cinema.videos.services.video_status_service import VideoStatusService
from apps.api.mixins import VersioningAPIViewMixin


class AudioTrackViewSet(
    VersioningAPIViewMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = AudioTrack.objects.all()
    filterset_class = AudioTrackFilter
    version_map = {
        "v1": {
            "serializer_class": AudioTrackSerializer
        }
    }

    @classmethod
    def _perform_update_and_create(cls, serializer):
        with transaction.atomic():
            instance = serializer.save()
            video = instance.video
            transaction.on_commit(
                partial(
                    VideoStatusService.rebuild_needed,
                    video,
                )
            )

    def perform_update(self, serializer):
        self._perform_update_and_create(serializer)

    def perform_create(self, serializer):
        self._perform_update_and_create(serializer)
