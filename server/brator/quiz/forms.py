import decimal

from .models import ChallengeFeedback, FeedbackType

from django import forms
from django.forms.widgets import NumberInput
from django.core.exceptions import ValidationError

class BooleanResponseForm(forms.Form):
    confidence_percent = forms.DecimalField(widget=NumberInput(), label="Confidence assertion is true (percent)", required=False)

    def clean(self):
        cleaned_data = super().clean()

        conf = cleaned_data.get("confidence_percent")
        
        if conf < 0 or conf > 100:
            raise ValidationError(f"Confidence percentage ({conf}) out of bounds")

        if conf >= 50:
            cleaned_data["answer"] = True
        else:
            cleaned_data["answer"] = False
            cleaned_data["confidence_percent"] = 100 - conf

        return cleaned_data

class NumericResponseForm(forms.Form):
    ci_low = forms.DecimalField(widget=NumberInput(), label="Low (estimated 5th percentile)", required=False)
    ci_high = forms.DecimalField(widget=NumberInput(), label="High (estimated 95th percentile)", required=False)

    def clean(self):
        cleaned_data = super().clean()

        low = cleaned_data.get("ci_low")
        high = cleaned_data.get("ci_high")

        if low > high:
            raise ValidationError(f"Lower-bound estimate cannot be bigger than higher-bound estimate")

        cleaned_data["confidence_percent"] = 90
        
        return cleaned_data

class ChallengeFeedbackForm(forms.Form):
    category = forms.ChoiceField(choices=FeedbackType.choices)
    text = forms.CharField(max_length=4 * 1024, widget=forms.Textarea)

class DeleteMyAccountForm(forms.Form):
    desired_confirmation_message = "Delete my account. I understand that this action is irreversible."
    confirmation_message = forms.CharField(max_length=128)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["confirmation_message"] != self.desired_confirmation_message:
            raise ValidationError(f"Confirmation message must be exactly {repr(self.desired_confirmation_message)}.")

        return cleaned_data

CHALLENGE_FORMS = {
    "boolean": BooleanResponseForm,
    "numeric": NumericResponseForm,
}
