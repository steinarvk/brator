from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from .models import Fact
from .serializers import FactSerializer, ChallengeSerializer

from .logic import get_or_create_current_challenge
from .logic import discard_current_challenge

from rest_framework import viewsets
from rest_framework import permissions

class FactViewSet(viewsets.ModelViewSet):
    queryset = Fact.objects.all().order_by("creation_time")
    serializer_class = FactSerializer
    permission_classes = [permissions.IsAdminUser]

class GameViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def challenge(self, request):
        user = self.request.user
        challenge = get_or_create_current_challenge(user)
        return Response(ChallengeSerializer(challenge).data)

    @challenge.mapping.delete
    def discard_current_challenge(self, request):
        user = self.request.user
        discard_current_challenge(user)
        return Response(status = status.HTTP_200_OK)
