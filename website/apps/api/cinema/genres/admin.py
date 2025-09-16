from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import Genre


@admin.register(Genre)
class GenreAdmin(GuardedModelAdmin):
    pass
