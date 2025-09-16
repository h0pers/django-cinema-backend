from rest_framework.serializers import ModelSerializer

from apps.api.cinema.genres.models import Genre


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = [
            "name",
            "slug",
        ]
