from django import forms


class LinkForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(),
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(),
    )
