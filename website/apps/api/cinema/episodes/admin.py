from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import Episode


class EpisodeTabularInline(admin.TabularInline):
    model = Episode


@admin.register(Episode)
class EpisodeAdmin(GuardedModelAdmin):
    pass
