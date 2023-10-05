from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import reverse
from ethstakersclub import views


class StaticViewSitemap(Sitemap):
    changefreq = 'always'
    priority = 1.0
    protocol = 'https'

    def items(self):
        return ["dashboard_empty", "attestation_live_monitoring_empty", "sync_live_monitoring_empty", "show_clients", "show_slots", "show_epochs", "show_validators", "settings"]
    def location(self, item):
        return reverse(item)

handler404 = 'frontend.views.handler404'

sitemaps = {
    'static': StaticViewSitemap
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('frontend.urls')),
    path('user/', include('allauth.urls')),
    path('user/', include('users.urls')),
    path('captcha/', include('captcha.urls')),
    path('', include('pwa.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, 'sitemap'),
    path('robots.txt', views.custom_robots_txt, name='custom_robots_txt'),
]
