from django.urls import path, re_path
from .views import settings, show_epoch, landing_page, show_validators, show_epochs, sync_live_monitoring_empty, attestation_live_monitoring_empty, show_slot, view_validator, show_slots, search_results, search_validator_results, dashboard_empty, attestation_live_monitoring, sync_live_monitoring

urlpatterns = [
    path('validator/<str:index>/', view_validator, name='view_validator'),
    path('slots/', show_slots, name='show_slots'),
    path('epochs/', show_epochs, name='show_epochs'),
    path('validators/', show_validators, name='show_validators'),
    path('search-results/', search_results, name='search_results'),
    path('search-validator-results/', search_validator_results, name='search_validator_results'),
    re_path(r'^dashboard/?$', dashboard_empty, name='dashboard_empty'),
    path('dashboard/attestation_live_monitoring/', attestation_live_monitoring_empty, name='attestation_live_monitoring_empty'),
    path('dashboard/<str:index>/attestation_live_monitoring/', attestation_live_monitoring, name='attestation_live_monitoring'),
    path('dashboard/sync_live_monitoring/', sync_live_monitoring_empty, name='sync_live_monitoring_empty'),
    path('dashboard/<str:index>/', view_validator, name='view_validator'),
    path('dashboard/<str:index>/sync_live_monitoring/', sync_live_monitoring, name='sync_live_monitoring'),
    path('slot/<int:slot_number>', show_slot, name='show_slot'),
    path('epoch/<int:epoch>', show_epoch, name='show_epoch'),
    path('settings/', settings, name='settings'),
    path('', landing_page, name='landing_page'),
]
