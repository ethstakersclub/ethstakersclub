from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser
from allauth.account.forms import SignupForm
from captcha.fields import CaptchaField


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('email',)


class CustomSignupForm(SignupForm):
    captcha = CaptchaField()