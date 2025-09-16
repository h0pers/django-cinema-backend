from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.api.cinema.seasons.models import Season


class SeasonSerializer(serializers.ModelSerializer):
    episodes_count = serializers.IntegerField(source="episodes.count", read_only=True)

    class Meta:
        model = Season
        fields = '__all__'
        read_only_fields = [
            "allowed_to_watch",
        ]

    def validate_title(self, value):
        if not value.is_show:
            raise ValidationError(_("Title not show type"))
        return value
