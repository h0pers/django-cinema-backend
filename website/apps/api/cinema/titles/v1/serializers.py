
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.api.cinema.crew.models import CrewMember
from apps.api.cinema.genres.models import Genre
from apps.api.cinema.genres.v1.serializers import GenreSerializer
from apps.api.cinema.titles.models import Title, TitleCrewMember
from apps.api.cinema.videos.models import Video
from apps.api.languages.v1.serializers import LanguageSerializer
from apps.core.models import Language


class CrewMemberRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = [
            "id",
            "full_name",
            "picture",
            "slug",
        ]


class TitleCrewMemberSerializer(serializers.ModelSerializer):
    crew_member_id = serializers.PrimaryKeyRelatedField(
        queryset=CrewMember.objects.all(),
        source="crew_member",
        write_only=True,
    )
    crew_member = CrewMemberRelatedSerializer(read_only=True)

    class Meta:
        model = TitleCrewMember
        fields = '__all__'


class TitleSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)
    languages_codes = serializers.SlugRelatedField(
        slug_field="code",
        write_only=True,
        many=True,
        required=False,
        queryset=Language.objects.all(),
        source="languages",
    )
    genres = GenreSerializer(many=True, read_only=True)
    genres_codes = serializers.SlugRelatedField(
        slug_field="slug",
        write_only=True,
        many=True,
        required=False,
        queryset=Genre.objects.all(),
        source="genres",
    )
    seasons_count = serializers.IntegerField(source="seasons.count", read_only=True)

    class Meta:
        model = Title
        fields = "__all__"
        read_only_fields = [
            "allowed_to_watch",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        title_type = attrs.get("type", getattr(self.instance, "type", None))
        video = attrs.get("video", getattr(self.instance, "video", None))

        if video is not None and title_type != Title.TitleType.MOVIE:
            raise ValidationError({
                "video": _("Video can not be assigned to a non-movie title")
            })

        if attrs.get("release_date") is not None and attrs.get("release_year") is not None:
            raise ValidationError({"message": _("Provide release date or release year")})

        if self.instance is not None and "release_year" in attrs:
            has_date_now = getattr(self.instance, "release_date", None) is not None
            touching_date = "release_date" in attrs
            if has_date_now and not touching_date:
                raise ValidationError({
                    "release_year": _("Change release date or set it to null to change release year")
                })

        return attrs

    def validate_video(self, value):
        if (
            value is not None and
            value.role != Video.Role.MOVIE
        ):
            raise ValidationError(_("Video is not of movie type"))
        return value

    def validate_trailer(self, value):
        if (
            value is not None and
            value.role != Video.Role.TRAILER
        ):
            raise ValidationError(_("Video is not of trailer type"))

        return value
