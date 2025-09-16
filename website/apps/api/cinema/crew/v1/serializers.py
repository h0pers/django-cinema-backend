from rest_framework import serializers

from apps.api.cinema.crew.models import CrewMember


class CrewMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = '__all__'
