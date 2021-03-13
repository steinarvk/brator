from rest_framework.exceptions import APIException

class BadRequest(APIException):
    status_code = 400
    default_detail = "Bad request."

class AlreadyResponded(APIException):
    status_code = 409
    default_detail = "Already responded."

class NoFactsAvailable(APIException):
    status_code = 500
    default_detail = "No facts available."
