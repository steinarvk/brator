from rest_framework.exceptions import APIException

class BadRequest(APIException):
    status_code = 400

class AlreadyResponded(APIException):
    status_code = 409
