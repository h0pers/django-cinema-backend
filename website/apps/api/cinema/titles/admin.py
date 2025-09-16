from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from apps.api.cinema.seasons.admin import SeasonTabularInline

from .models import Title, TitleCrewMember


class TitleCrewMemberTabularInline(admin.TabularInline):
    model = TitleCrewMember


@admin.register(Title)
class TitleAdmin(GuardedModelAdmin):
    inlines = [
        SeasonTabularInline,
        TitleCrewMemberTabularInline,
    ]
