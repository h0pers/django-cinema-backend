
from rest_framework.permissions import BasePermission

from apps.api.cinema.episodes.models import Episode
from apps.api.cinema.titles.models import Title
from apps.api.cinema.videos.models import Video


class WatchPermission(BasePermission):
    """
    Permission to view a Video asset (movie/episode/trailer).

    Enforcement order (short-circuit, cheapest first):
      1) If a user is superuser or staff -> allow.
      2) Resolve binding (movie / episode / trailer). If broke -> deny.
      3) If Title is DRAFT and user is not staff -> deny (even if Video is PUBLIC).
      4) If Video is PUBLIC -> allow (after a DRAFT gate).
      5) If a user is anonymous -> deny (protected content requires auth).
      6) Enforce allowed_to_watch toggles for non-staff users (customers):
         - Movie/Trailer: title.allowed_to_watch must be True.
         - Episode: all of episode/season/title.allowed_to_watch must be True.
      7) Global (model-level) permissions -> allow.
      8) Object permissions on title/episode/season -> allow.
      9) Genre-based permissions (if any title genre matches) -> allow.
     10) Otherwise -> deny.

    Notes:
      - This class assumes an object-permissions backend is configured
        (e.g., django-guardian) so `user.has_perm(codename, obj)` works.
    """
    PERM_WATCH_ALL = "cinema.can_watch_all"
    PERM_WATCH_ALL_MOVIES = "cinema.can_watch_all_movies"
    PERM_WATCH_ALL_SHOWS = "cinema.can_watch_all_shows"
    PERM_WATCH_TITLE = "cinema.can_watch_title"
    PERM_WATCH_SEASON = "cinema.can_watch_season"
    PERM_WATCH_EPISODE = "cinema.can_watch_episode"
    PERM_WATCH_GENRE = "cinema.can_watch_genre"
    PERM_WATCH_GENRE_MOVIES = "cinema.can_watch_genre_movies"
    PERM_WATCH_GENRE_SHOWS = "cinema.can_watch_genre_shows"

    def has_object_permission(self, request, view, obj: Video) -> bool:
        user = request.user

        # Admin overrides
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        # Resolve video context (title / episode)
        is_movie = getattr(obj, "attached_as_movie", False)
        is_episode = getattr(obj, "attached_as_episode", False)
        is_trailer = getattr(obj, "attached_as_trailer", False)

        title: Title | None = None
        episode: Episode | None = None

        if is_movie:
            # Movie video is attached directly to a Title via related_name='as_movie'
            title = getattr(obj, "as_movie", None)
        elif is_episode:
            # Episode video is attached to an Episode via related_name='as_episode'
            episode = getattr(obj, "as_episode", None)
            if episode is not None:
                season = getattr(episode, "season", None)
                title = getattr(season, "title", None) if season is not None else None
        elif is_trailer:
            # Trailer video is attached to a Title via related_name='as_trailer'
            title = getattr(obj, "as_trailer", None)

        # If bindings are broken or missing, deny.
        if title is None and not is_episode:
            return False
        # At this point, either:
        #   - we have a title (movie/trailer), or
        #   - we have an episode (and thus title resolved or not). If the title is still
        #     None for an episode, consider it broken data and deny.
        if is_episode and (episode is None or title is None):
            return False

        # Title draft gate (blocks non-staff even for PUBLIC videos)
        # Staff can see draft content.
        if getattr(title, "draft", False) and not getattr(user, "is_staff", False):
            return False

        # PUBLIC videos bypass (after the draft gate)
        # PUBLIC means "no permission checks" apart from the draft rule above.
        if getattr(obj, "public", False):
            return True

        # Anonymous users cannot access protected content
        if not getattr(user, "is_authenticated", False):
            return False

        # allowed_to_watch toggles (customers only; staff already passed)
        if is_movie or is_trailer:
            if not getattr(title, "allowed_to_watch", True):
                return False
        elif is_episode and episode is not None:
            season = getattr(episode, "season", None)
            if (
                not getattr(episode, "allowed_to_watch", True)
                or not getattr(season, "allowed_to_watch", True)
                or not getattr(title, "allowed_to_watch", True)
            ):
                return False

        # Global (model-level) permissions
        if user.has_perm(self.PERM_WATCH_ALL):
            return True
        if (is_movie or is_trailer) and user.has_perm(self.PERM_WATCH_ALL_MOVIES):
            return True
        if is_episode and user.has_perm(self.PERM_WATCH_ALL_SHOWS):
            return True

        # Object-level permissions
        # Title-level
        if title is not None and user.has_perm(self.PERM_WATCH_TITLE, title):
            return True

        # Episode/Season-level (for shows)
        if is_episode and episode is not None:
            if user.has_perm(self.PERM_WATCH_EPISODE, episode):
                return True
            season = getattr(episode, "season", None)
            if season is not None and user.has_perm(self.PERM_WATCH_SEASON, season):
                return True

        # Genre-based permissions
        # If a user has any matching genre permission for the title's genres, allow.
        try:
            genres_iter = getattr(title, "genres", None)
            if genres_iter is not None:
                for genre in genres_iter.all():
                    if user.has_perm(self.PERM_WATCH_GENRE, genre):
                        return True
                    if (is_movie or is_trailer) and user.has_perm(self.PERM_WATCH_GENRE_MOVIES, genre):
                        return True
                    if is_episode and user.has_perm(self.PERM_WATCH_GENRE_SHOWS, genre):
                        return True
        except Exception:
            # Be conservative on unexpected relation errors.
            pass

        # Fallback: deny
        return False
