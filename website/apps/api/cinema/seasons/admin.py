from django.contrib import admin

from .models import Season


class SeasonTabularInline(admin.TabularInline):
    model = Season
