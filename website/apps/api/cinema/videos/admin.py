from django.contrib import admin

from apps.api.cinema.audio_tracks.admin import AudioTrackInline

from .models import Video, VideoResolution


class VideoResolutionInline(admin.TabularInline):
    model = VideoResolution
    # readonly_fields = ["status", "file_name"]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ["hls_decrypt_key"]
    inlines = [
        AudioTrackInline,
        VideoResolutionInline,
    ]
