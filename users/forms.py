from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('email',)