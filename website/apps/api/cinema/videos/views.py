from functools import partial

from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from library.aws.client.s3 import S3StorageClient
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.permissions import DjangoModelPermissions, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.cinema.audio_tracks.filters import AudioTrackFilter
from apps.api.cinema.audio_tracks.models import AudioTrack
from apps.api.cinema.audio_tracks.v1.serializers import AudioTrackSerializer
from apps.api.cinema.videos.filters import VideoFilterSet
from apps.api.cinema.videos.models import Video
from apps.api.cinema.videos.permissions import WatchPermission
from apps.api.cinema.videos.services.video_status_service import VideoStatusService
from apps.api.cinema.videos.tasks import create_master_playlist
from apps.api.cinema.videos.v1.serializers import (
    PlaybackSerializer,
    VideoCreateSerializer,
    VideoSerializer,
)
from apps.api.mixins import VersioningAPIViewMixin


class VideoViewSet(
    VersioningAPIViewMixin,
    ModelViewSet,
):
    queryset = Video.objects.all()
    filterset_class = VideoFilterSet
    permission_classes = [IsAdminUser, DjangoModelPermissions]
    version_map = {
        "v1": {
            "serializer_class": VideoSerializer
        }
    }

    def get_version_map(self):
        if self.action in ("create",):
            return {
                "v1": {
                    "serializer_class": VideoCreateSerializer
                }
            }
        return super().get_version_map()

    def perform_create(self, serializer):
        obj = serializer.save()
        base_url = self.request.build_absolute_uri("/")
        transaction.on_commit(partial(
            create_master_playlist.delay,
            base_url=base_url,
            video_id=obj.id
        ))

    def perform_update(self, serializer):
        instance = serializer.save()
        transaction.on_commit(partial(
            VideoStatusService.rebuild_needed,
            instance,
        ))

    def get_queryset(self):
        pk = self.kwargs.get("pk", None)

        if self.action == "audio_tracks":
            return AudioTrack.objects.filter(video=pk)

        return super().get_queryset()

    @action(
        detail=True,
        methods=["GET"],
        permission_classes=[WatchPermission],
        version_map={
            "v1": {
                "serializer_class": PlaybackSerializer,
            }
        }
    )
    def playback(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[IsAdminUser],
        version_map=None,
    )
    def rebuild(self, request, *args, **kwargs):
        obj = self.get_object()

        self.check_object_permissions(request, obj)

        if obj.processing:
            raise ValidationError({"video": _("Video is processing now")})

        if not obj.has_default_audio:
            raise ValidationError({"audio_tracks": _("No default audio track found")})

        base_url = request.build_absolute_uri("/")
        create_master_playlist.delay(
            base_url = base_url,
            video_id = obj.id
        )
        return Response({"status": _("Master playlist rebuild scheduled")})

    @action(
        detail=True,
        methods=["GET"],
        filterset_class=AudioTrackFilter,
        url_path="audio-tracks",
        version_map={
            "v1": {
                "serializer_class": AudioTrackSerializer,
            }
        }
    )
    def audio_tracks(self, request, pk, *args, **kwargs):
        video = get_object_or_404(Video, id=pk)

        self.check_object_permissions(request, video)

        return self.list(request, *args, **kwargs)


class HLSKeyAPIView(RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [WatchPermission]

    def retrieve(self, request, *args, **kwargs):
        video = self.get_object()
        if not video.encrypted:
            raise ValidationError({"hls_decrypt_key": _("This video is not encrypted")})

        key = str(video.hls_decrypt_key)

        storage_client = S3StorageClient()
        url = storage_client.storage.url(key, expire=30)

        return redirect(url, permanent=True)
