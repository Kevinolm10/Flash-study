from django.contrib import admin
from .models import Deck, Card, StudySession, UserProfile, StudyNote

@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['question', 'deck', 'ease_factor', 'interval', 'repetitions', 'created_at']
    list_filter = ['deck', 'created_at', 'ease_factor']
    search_fields = ['question', 'answer']
    readonly_fields = ['ease_factor', 'interval', 'repetitions']

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'card', 'difficulty', 'studied_at', 'next_review', 'response_time']
    list_filter = ['difficulty', 'studied_at']
    readonly_fields = ['next_review']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_cards_studied', 'current_streak', 'longest_streak', 'last_study_date']
    list_filter = ['last_study_date']
    readonly_fields = ['total_cards_studied', 'total_study_time', 'current_streak', 'longest_streak']

@admin.register(StudyNote)
class StudyNoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'card', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['content']