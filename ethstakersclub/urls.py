from django.contrib import admin
from django.urls import path, include

handler404 = 'frontend.views.handler404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('frontend.urls')),
    path('user/', include('allauth.urls')),
    path('user/', include('users.urls')),
    path('captcha/', include('captcha.urls')),
    path('', include('pwa.urls')),
]
