from apps.api.cinema.videos.models import Video


class VideoStatusService:
    @classmethod
    def rebuild_needed(cls, video: Video):
        video.rebuild_needed = True
        video.save()

    @staticmethod
    def completed(video: Video):
        video.status = Video.Status.COMPLETED
        video.rebuild_needed = False
        video.save()

    @staticmethod
    def processing(video: Video):
        video.status = Video.Status.PROCESSING
        video.save()

    @staticmethod
    def failed(video: Video):
        video.status = Video.Status.FAILED
        video.save()

    @staticmethod
    def created(video: Video):
        video.status = Video.Status.CREATED
        video.save()
