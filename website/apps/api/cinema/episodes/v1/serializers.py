from rest_framework import serializers

from apps.api.cinema.episodes.models import Episode


class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        exclude = [
            "allowed_to_watch",
        ]
