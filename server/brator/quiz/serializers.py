from .models import Fact, Challenge, BooleanChallenge, NumericChallenge, BooleanFact, NumericFact, BooleanResponse, NumericResponse, Response

from rest_framework import serializers

class StripNullsSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return {k: v for k, v in rep.items() if v is not None}

class BooleanFactFullSerializer(StripNullsSerializer):
    class Meta:
        model = BooleanFact
        fields = "__all__"

class NumericFactFullSerializer(StripNullsSerializer):
    class Meta:
        model = NumericFact
        fields = "__all__"

class FactFullSerializer(StripNullsSerializer):
    boolean_fact = BooleanFactFullSerializer()
    numeric_fact = NumericFactFullSerializer()

    class Meta:
        model = Fact
        fields = "__all__"

class ScoreSerializer(StripNullsSerializer):
    class Meta:
        model = Response
        fields = [
            "creation_time",
            "correct",
            "confidence_percent",
        ]

class FactChallengeSerializer(StripNullsSerializer):
    class Meta:
        model = Fact
        fields = [
            "id",
            "creation_time",
            "key",
        ]

class BooleanFactChallengeSerializer(StripNullsSerializer):
    class Meta:
        model = BooleanFact
        fields = ["question_text"]

class NumericFactChallengeSerializer(StripNullsSerializer):
    class Meta:
        model = NumericFact
        fields = ["question_text", "correct_answer_unit"]


class BooleanChallengeSerializer(StripNullsSerializer):
    fact = BooleanFactChallengeSerializer()

    class Meta:
        model = BooleanChallenge
        fields = ["fact"]

class NumericChallengeSerializer(StripNullsSerializer):
    fact = NumericFactChallengeSerializer()

    class Meta:
        model = NumericChallenge
        fields = ["fact"]

class ChallengeSerializer(StripNullsSerializer):
    fact = FactChallengeSerializer()
    boolean_challenge = BooleanChallengeSerializer()
    numeric_challenge = NumericChallengeSerializer()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "uid",
            "fact",
            "creation_time",
            "challenge_type",
            "boolean_challenge",
            "numeric_challenge",
        ]
