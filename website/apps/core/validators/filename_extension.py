from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class FilenameExtensionValidator(FileExtensionValidator):
    def __call__(self, value: str):
        extension = Path(value).suffix[1:].lower()
        if (
            self.allowed_extensions is not None
            and extension not in self.allowed_extensions
        ):
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "extension": extension,
                    "allowed_extensions": ", ".join(self.allowed_extensions),
                    "value": value,
                },
            )
