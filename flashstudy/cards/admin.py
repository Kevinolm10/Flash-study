from django.contrib import admin
from .models import Deck, Card, StudySession

@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['question', 'deck', 'created_at']
    list_filter = ['deck', 'created_at']
    search_fields = ['question', 'answer']

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'card', 'difficulty', 'studied_at', 'next_review']
    list_filter = ['difficulty', 'studied_at']