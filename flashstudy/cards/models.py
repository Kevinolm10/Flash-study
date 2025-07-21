from django.db import models
from django.contrib.auth.models import User

class Deck(models.Model):
    """A collection of flashcards"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class Card(models.Model):
    """Individual flashcard"""
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.question[:50]}..."
    
    class Meta:
        ordering = ['created_at']

class StudySession(models.Model):
    """Track study progress for spaced repetition"""
    DIFFICULTY_CHOICES = [
        (1, 'Again (< 1 min)'),
        (2, 'Hard (< 6 min)'),
        (3, 'Good (< 10 min)'),
        (4, 'Easy (4 days)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    studied_at = models.DateTimeField(auto_now_add=True)
    next_review = models.DateTimeField()
    
    def __str__(self):
        return f"{self.user.username} - {self.card.question[:30]}"
    
    class Meta:
        ordering = ['-studied_at']