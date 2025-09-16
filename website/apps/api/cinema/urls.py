from django.urls import include, path

app_name = "cinema"

urlpatterns = [
    path("titles/", include("apps.api.cinema.titles.urls")),
    path("seasons/", include("apps.api.cinema.seasons.urls")),
    path("episodes/", include("apps.api.cinema.episodes.urls")),
    path("audio-tracks/", include("apps.api.cinema.audio_tracks.urls")),
    path("videos/", include("apps.api.cinema.videos.urls")),
    path("crew/", include("apps.api.cinema.crew.urls")),
    path("genres/", include("apps.api.cinema.genres.urls")),
]
