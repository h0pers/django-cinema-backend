from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.api.uploads.models import LazyLoadFile


class LazyLoadFileSerializer(serializers.ModelSerializer):
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = LazyLoadFile
        exclude = [
            "file",
            "upload_id",
        ]
        read_only_fields = [
            "status",
            "file_name",
            "name",
        ]

    def get_file_type(self, obj):
        return obj.file_type


class RenameLazyLoadFileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[
            UniqueValidator(lookup="iexact", queryset=LazyLoadFile.objects.all()),
        ]
    )

    class Meta:
        model = LazyLoadFile
        fields = [
            "id",
            "name"
        ]


class InitUploadSerializer(serializers.ModelSerializer):
    file_size = serializers.IntegerField(
        validators=[
            MinValueValidator(1),
        ]
    )
    content_type = serializers.CharField(max_length=255)

    class Meta:
        model = LazyLoadFile
        exclude = [
            "file",
            "name",
            "status",
        ]

    def save(self, **kwargs):
        self.validated_data.pop("file_size")
        self.validated_data.pop("content_type")
        return super().save()


class InitUploadResponseSerializer(serializers.ModelSerializer):
    urls = serializers.ListField(
        child=serializers.URLField(),
    )

    class Meta:
        model = LazyLoadFile
        fields = [
            "id",
            "urls",
            "upload_id",
            "status",
        ]


class UploadCompletedSerializer(serializers.Serializer):
    etags = serializers.ListField(
        child=serializers.CharField(max_length=255),
    )
