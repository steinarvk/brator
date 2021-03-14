import json
import logging

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from ..models import Fact
from ..serializers import FactFullSerializer, ChallengeSerializer, ScoreSerializer

from ..logic import get_or_create_current_challenge
from ..logic import discard_current_challenge
from ..logic import respond_to_challenge
from ..logic import get_user_responses
from ..logic import post_fact

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
        facts = Fact.objects.all()
        data = FactFullSerializer(facts, many=True).data
        return Response(data)

    def create(self, request):
        fact_data = json.loads(self.request.body)
        logger.info("Creating fact: %s", repr(fact_data))
        fact = post_fact(fact_data)
        return Response(FactFullSerializer(fact).data)
