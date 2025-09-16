from apps.api.cinema.videos.models import ToggleWatchModel


class ToggleWatchService:
    @staticmethod
    def enable(obj: ToggleWatchModel):
        obj.allowed_to_watch = True
        obj.save()

    @staticmethod
    def disable(obj: ToggleWatchModel):
        obj.allowed_to_watch = False
        obj.save()
