from rest_framework import status
from rest_framework.response import Response as RestResponse
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if not response:
        response = RestResponse({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    exc_type = type(exc)
    response.data['type'] = f'{exc_type.__module__}.{exc_type.__name__}'

    return response
