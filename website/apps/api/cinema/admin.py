from .audio_tracks.admin import AudioTrackInline
from .crew.admin import CrewMemberAdmin
from .episodes.admin import EpisodeAdmin, EpisodeTabularInline
from .genres.admin import GenreAdmin
from .seasons.admin import SeasonTabularInline
from .titles.admin import TitleAdmin, TitleCrewMemberTabularInline
from .videos.admin import VideoAdmin, VideoResolutionInline

__all__ = [
    "TitleAdmin",
    "EpisodeAdmin",
    "EpisodeTabularInline",
    "TitleCrewMemberTabularInline",
    "VideoAdmin",
    "VideoResolutionInline",
    "AudioTrackInline",
    "SeasonTabularInline",
    "CrewMemberAdmin",
    "GenreAdmin",
]
