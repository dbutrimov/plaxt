from django import forms
from django.core.validators import RegexValidator


class ServerForm(forms.Form):
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(),
        validators=[
            RegexValidator(r'^https?:\/\/[^:/]+(:\d+)?\/?$'),
        ]
    )
