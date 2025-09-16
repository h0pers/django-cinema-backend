from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator

from apps.core.models import Language


class LanguageSerializer(ModelSerializer):
    code = serializers.CharField(
        validators=[
            UniqueValidator(lookup="iexact", queryset=Language.objects.all()),
        ]
    )
    name = serializers.CharField(
        validators=[
            UniqueValidator(lookup="iexact", queryset=Language.objects.all()),
        ]
    )

    class Meta:
        model = Language
        fields = [
            "name",
            "code",
        ]
