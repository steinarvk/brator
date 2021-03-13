from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.core.exceptions import ValidationError

def api_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        try:
            raise APIException(status_code=400, detail="Validation failed.") from exc
        except Exception as exc:
            response = exception_handler(exc, context)
    else:
        response = exception_handler(exc, context)

    return response
