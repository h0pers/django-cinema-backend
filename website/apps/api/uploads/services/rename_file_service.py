
from apps.api.uploads.models import LazyLoadFile


class RenameLazyFileService:
    @staticmethod
    def rename(name: str, obj: LazyLoadFile):
        obj.name = name
        obj.save()
