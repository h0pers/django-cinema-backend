from django.db import models
from django.db.models.functions import Lower

from apps.core.models import UniqueNamedModel


class Language(UniqueNamedModel):
    code = models.CharField(max_length=20, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta(UniqueNamedModel.Meta):
        constraints = [
            *UniqueNamedModel.Meta.constraints,
            models.UniqueConstraint(
                Lower("code"),
                name="unique_language_code"
            )
        ]
