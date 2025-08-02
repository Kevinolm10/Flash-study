from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import math

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

    # Spaced repetition fields
    ease_factor = models.FloatField(default=2.5)  # Initial ease factor
    interval = models.IntegerField(default=1)  # Days until next review
    repetitions = models.IntegerField(default=0)  # Number of successful repetitions

    def __str__(self):
        return f"{self.question[:50]}..."

    def get_next_review_date(self, quality):
        """
        Calculate next review date based on SM-2 algorithm
        quality: 0-5 (0=total blackout, 5=perfect response)
        """
        if quality < 3:
            # Reset if quality is poor
            self.repetitions = 0
            self.interval = 1
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = math.ceil(self.interval * self.ease_factor)

            self.repetitions += 1

        # Update ease factor
        self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        return timezone.now() + timedelta(days=self.interval)

    def is_due_for_review(self, user):
        """Check if card is due for review for a specific user"""
        try:
            latest_session = self.studysession_set.filter(user=user).latest('studied_at')
            return timezone.now() >= latest_session.next_review
        except StudySession.DoesNotExist:
            return True  # Never studied, so it's due

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

    # Quality mapping for SM-2 algorithm
    QUALITY_MAPPING = {
        1: 0,  # Again -> Total blackout
        2: 2,  # Hard -> Incorrect response, correct one remembered
        3: 4,  # Good -> Correct response with hesitation
        4: 5,  # Easy -> Perfect response
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    studied_at = models.DateTimeField(auto_now_add=True)
    next_review = models.DateTimeField()
    response_time = models.FloatField(null=True, blank=True)  # Time taken to answer in seconds

    def save(self, *args, **kwargs):
        """Override save to calculate next review date"""
        if not self.next_review:
            quality = self.QUALITY_MAPPING.get(self.difficulty, 3)
            self.next_review = self.card.get_next_review_date(quality)
            self.card.save()  # Save updated card fields
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.card.question[:30]}"

    @classmethod
    def get_due_cards(cls, user, deck=None):
        """Get all cards due for review for a user"""
        from django.db.models import Q, Max

        # Get cards that have never been studied or are due for review
        studied_cards = cls.objects.filter(user=user).values('card').annotate(
            last_review=Max('next_review')
        ).filter(last_review__lte=timezone.now()).values_list('card', flat=True)

        never_studied = Card.objects.exclude(
            id__in=cls.objects.filter(user=user).values_list('card', flat=True)
        )

        due_cards_query = Q(id__in=studied_cards) | Q(id__in=never_studied)

        if deck:
            due_cards_query &= Q(deck=deck)

        return Card.objects.filter(due_cards_query).order_by('?')  # Random order

    class Meta:
        ordering = ['-studied_at']
        unique_together = ['user', 'card', 'studied_at']  # Prevent duplicate sessions


class UserProfile(models.Model):
    """Extended user profile for study statistics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_cards_studied = models.IntegerField(default=0)
    total_study_time = models.FloatField(default=0.0)  # in minutes
    current_streak = models.IntegerField(default=0)  # days
    longest_streak = models.IntegerField(default=0)  # days
    last_study_date = models.DateField(null=True, blank=True)
    preferred_daily_cards = models.IntegerField(default=20)

    def update_streak(self):
        """Update study streak based on last study date"""
        today = timezone.now().date()

        if self.last_study_date:
            days_diff = (today - self.last_study_date).days

            if days_diff == 1:
                # Studied yesterday, continue streak
                self.current_streak += 1
            elif days_diff > 1:
                # Missed days, reset streak
                self.current_streak = 1
            # If days_diff == 0, already studied today, don't change streak
        else:
            # First time studying
            self.current_streak = 1

        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_study_date = today
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Profile"


class StudyNote(models.Model):
    """User notes for study sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note by {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']