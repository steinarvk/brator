import decimal

from django import forms
from django.forms.widgets import NumberInput
from django.core.exceptions import ValidationError

MAX_CONFIDENCE = decimal.Decimal("99.99")
MIN_CONFIDENCE = decimal.Decimal( "0.01")

class RangeInput(NumberInput):
    input_type = 'range'

class BooleanResponseForm(forms.Form):
    answer = forms.ChoiceField(choices=[
        ("False", "False"),
        ("True", "True"),
    ], label="Answer")
    confidence_percent = forms.DecimalField(widget=RangeInput(), label="Confidence (percent)")

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("confidence_percent") == 100:
            cleaned_data["confidence_percent"] = MAX_CONFIDENCE

        conf = cleaned_data.get("confidence_percent")
        
        if conf < 50 or conf >= 100:
            raise ValidationError(f"Confidence percentage ({conf}) out of bounds [50, 100>")

        return cleaned_data

class NumericResponseForm(forms.Form):
    ci_low = forms.DecimalField(widget=NumberInput(), label="Low (estimated 5th percentile)")
    ci_high = forms.DecimalField(widget=NumberInput(), label="High (estimated 95th percentile)")

    def clean(self):
        cleaned_data = super().clean()

        low = cleaned_data.get("ci_low")
        high = cleaned_data.get("ci_high")

        if low > high:
            raise ValidationError(f"Lower-bound estimate cannot be bigger than higher-bound estimate")

        cleaned_data["confidence_percent"] = 90
        
        return cleaned_data

CHALLENGE_FORMS = {
    "boolean": BooleanResponseForm,
    "numeric": NumericResponseForm,
}
