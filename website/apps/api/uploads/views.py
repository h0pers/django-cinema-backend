from botocore.exceptions import ClientError
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import LazyFileFilterSet
from .models import LazyLoadFile
from .services.rename_file_service import RenameLazyFileService
from .services.upload_file_service import UploadFileService
from .v1.serializers import (
    InitUploadResponseSerializer,
    InitUploadSerializer,
    LazyLoadFileSerializer,
    RenameLazyLoadFileSerializer,
    UploadCompletedSerializer,
)


class UploadViewSet(
    VersioningAPIViewMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = LazyLoadFile.objects.all()
    permission_classes = [IsAdminUser]
    filterset_class = LazyFileFilterSet
    version_map = {
        "v1": {
            "serializer_class": LazyLoadFileSerializer,
        }
    }
    @action(
        detail=True,
        methods=["POST"],
        version_map={
            "v1": {
                "serializer_class": UploadCompletedSerializer
            }
        }
    )
    def complete(self, request, *args, **kwargs):
        obj = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        etags = serializer.validated_data["etags"]

        file_upload_service = UploadFileService()

        if not obj.loading:
            raise ValidationError({"status": _("Video is not loading")})

        try:
            file_upload_service.complete(obj, etags)
        except ClientError:
            return Response({"message": _("At least one chunk of the file needs to be uploaded")})

        return Response({"message": _("Video upload completed")})

    @action(
        detail=True,
        methods=["POST"],
    )
    def abort(self, request, *args, **kwargs):
        obj = self.get_object()
        file_upload_service = UploadFileService()
        if not obj.loading:
            raise ValidationError({"status": _("Video is not loading")})
        file_upload_service.abort(obj)
        serializer = self.get_serializer(instance=obj)
        return Response(serializer.data)

    @action(
        methods=["POST"],
        detail=False,
        version_map={
            "v1": {
                "serializer_class": InitUploadSerializer,
            }
        }
    )
    def init(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_upload_service = UploadFileService()

        file_name = serializer.validated_data["file_name"]
        file_size = serializer.validated_data["file_size"]
        content_type = serializer.validated_data["content_type"]

        file, multipart = file_upload_service.upload(
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
        )
        file.urls = multipart.urls
        serializer = InitUploadResponseSerializer(instance=file)
        return Response(serializer.data)

    @action(
        methods=["POST"],
        detail=True,
        version_map={
            "v1": {
                "serializer_class": RenameLazyLoadFileSerializer,
            }
        }
    )
    def rename(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not obj.completed:
            raise ValidationError({"status": _("Video is not completed")})

        file_name = serializer.validated_data["name"]
        RenameLazyFileService.rename(file_name, obj)

        serializer = self.get_serializer(instance=obj)

        return Response(serializer.data)
