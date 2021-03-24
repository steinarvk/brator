import json
import functools
import base64
import logging

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import APIException

from ..models import Fact
from ..serializers import FactFullSerializer, ChallengeSerializer, ScoreSerializer

from ..logic import get_or_create_current_challenge
from ..logic import discard_current_challenge
from ..logic import respond_to_challenge
from ..logic import get_user_responses
from ..logic import post_fact
from ..logic import export_facts
from ..logic import export_fact_categories
from ..logic import post_fact_category

from rest_framework import viewsets
from rest_framework import permissions

logger = logging.getLogger(__name__)

class GameViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["GET"], url_name="challenge")
    def challenge(self, request):
        user = self.request.user
        challenge = get_or_create_current_challenge(user)
        return Response(ChallengeSerializer(challenge).data)

    @challenge.mapping.delete
    def discard_current_challenge(self, request):
        user = self.request.user
        discard_current_challenge(user)
        return Response(status = status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="challenges/(?P<challenge_uid>[0-9a-f]+)/response", url_name="response")
    def response(self, request, challenge_uid):
        user = self.request.user
        response = json.loads(self.request.body)
        respond_to_challenge(user, challenge_uid, response)
        challenge = get_or_create_current_challenge(user)
        return Response(ChallengeSerializer(challenge).data)

class EvalViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["GET"], url_name="scores")
    def scores(self, request):
        user = self.request.user
        responses = get_user_responses(user, limit=1000)
        return Response(ScoreSerializer(responses, many=True).data)

class FactViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        facts = Fact.objects.select_related("boolean_fact", "numeric_fact").all()
        data = FactFullSerializer(facts, many=True).data
        return Response(data)

    def create(self, request):
        fact_data = json.loads(self.request.body)
        logger.info("Creating fact: %s", repr(fact_data))
        fact = post_fact(fact_data)
        return Response(FactFullSerializer(fact).data)

def api_view(f):
    @functools.wraps(f)
    def wrapped(request, *args, **kwargs):
        try:
            if "HTTP_AUTHORIZATION" in request.META:
                method, creds = request.META["HTTP_AUTHORIZATION"].split()
                assert method.lower() == "basic"
                username, password = base64.b64decode(creds).decode().split(":")
                user = authenticate(username=username, password=password)
                if user and user.is_active:
                    login(request, user)
                    request.user = user

            return f(request, *args, **kwargs)
        except APIException as e:
            logger.exception(f"Returning HTTP {e.status_code}")
            return HttpResponse(
                json.dumps({
                    "ok": False,
                    "status": "error",
                    "error_message": e.detail,
                    "status_code": e.status_code,
                }, indent=4),
                content_type = "application/json",
                status = e.status_code,
            )
    return wrapped

@api_view
def export_facts_view(request):
    data = export_facts(request.user)
    serialized = json.dumps(data, indent="  ")
    return HttpResponse(
        serialized,
        content_type = "application/json",
    )

@api_view
@csrf_exempt
def import_facts_view(request):
    if not request.user.is_staff:
        return HttpResponse("Permission denied", status_code=403)

    if not request.method == "POST":
        return HttpResponse("Wrong method", status_code=405)
        
    fact_data = json.loads(request.body)
    logger.info("Import body is: %d %s", len(fact_data), type(fact_data))
    if isinstance(fact_data, dict):
        fact_data = [fact_data]

    for x in fact_data:
        logger.info("Posting fact: %s", repr(x))
        resp = post_fact(x)
        logger.info("Posted fact: %s ==> %s", repr(x), repr(resp))

    rv = {"imported": len(fact_data)}

    serialized = json.dumps(rv, indent="  ")

    return HttpResponse(
        serialized,
        content_type = "application/json",
    )

@api_view
def export_fact_categories_view(request):
    data = export_fact_categories(request.user)
    serialized = json.dumps(data, indent="  ")
    return HttpResponse(
        serialized,
        content_type = "application/json",
    )

@api_view
@csrf_exempt
def import_fact_categories_view(request):
    if not request.user.is_staff:
        return HttpResponse("Permission denied", status_code=403)

    if not request.method == "POST":
        return HttpResponse("Wrong method", status_code=405)
        
    factcat_data = json.loads(request.body)
    logger.info("Import body is: %d %s", len(factcat_data), type(factcat_data))
    if isinstance(factcat_data, dict):
        factcat_data = [factcat_data]

    for x in factcat_data:
        logger.info("Posting factcat: %s", repr(x))
        resp = post_fact_category(x)
        logger.info("Posted factcat: %s ==> %s", repr(x), repr(resp))

    rv = {"imported": len(factcat_data)}

    serialized = json.dumps(rv, indent="  ")

    return HttpResponse(
        serialized,
        content_type = "application/json",
    )
