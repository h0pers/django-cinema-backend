from django.contrib import admin

from .models import AudioTrack


class AudioTrackInline(admin.TabularInline):
    model = AudioTrack
    readonly_fields = ["hls_file"]
