from django.urls import path
from .views import save_watched_validators

urlpatterns = [
    path('save_watched_validators/', save_watched_validators, name='save_watched_validators'),
]
