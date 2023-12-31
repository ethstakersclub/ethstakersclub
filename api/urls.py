from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('blocks_by_proposer/', views.api_get_blocks_by_proposer, name='api_get_blocks_by_proposer'),
    path('blocks/', views.get_blocks, name='get_blocks'),
    path('epochs/', views.get_epochs, name='get_epochs'),
    path('attestations_for_slots/', views.api_get_attestations_for_slots, name='api_get_attestations_for_slots'),
    path('attestations/', views.api_get_attestations, name='api_get_attestations'),
    path('withdrawals/', views.api_get_withdrawals, name='api_get_withdrawals'),
    path('sync_committee_participation/', views.api_get_sync_committee_participation, name='api_get_sync_committee_participation'),
    path('rewards_and_penalties/', views.api_get_rewards_and_penalties, name='api_get_rewards_and_penalties'),
    path('chart_data/', views.api_chart_data_daily_rewards, name='api_chart_data_daily_rewards'),
    path('validators_by_id/', views.api_get_validators_by_id, name='api_get_validators_by_id'),
    path('validators/', views.api_get_validators, name='api_get_validators'),
    path('check_if_proposal_scheduled/', views.check_if_proposal_scheduled, name='check_if_proposal_scheduled'),
    path('current_beacon_state/', views.get_current_beacon_state, name='get_current_beacon_state'),
]