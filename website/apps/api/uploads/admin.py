from django.contrib import admin

from .models import LazyLoadFile


@admin.register(LazyLoadFile)
class LazyLoadFileAdmin(admin.ModelAdmin):
    readonly_fields = ["id"]
