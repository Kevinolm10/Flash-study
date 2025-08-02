from django.urls import path
from . import views

urlpatterns = [
    # Main study page
    path('', views.homePage, name='cards'),

    # API endpoints
    path('api/cards/', views.api_cards, name='api_cards'),
    path('api/study-session/', views.api_study_session, name='api_study_session'),
    path('api/notes/', views.api_save_note, name='api_save_note'),

    # Additional views
    path('statistics/', views.study_statistics, name='study_statistics'),
    path('deck/<int:deck_id>/', views.deck_view, name='deck_view'),
]