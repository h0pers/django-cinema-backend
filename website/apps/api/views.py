from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if isinstance(exc, ProtectedError):
        return Response({
            "message": _("This object cannot be deleted because it is referenced by other records")},
            status=status.HTTP_409_CONFLICT,
        )
    return response
