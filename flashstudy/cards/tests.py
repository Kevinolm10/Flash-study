from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Deck, Card, StudySession, UserProfile, StudyNote


class CardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deck = Deck.objects.create(name='Test Deck', owner=self.user)
        self.card = Card.objects.create(
            deck=self.deck,
            question='What is 2+2?',
            answer='4'
        )

    def test_card_creation(self):
        """Test that cards are created with correct default values"""
        self.assertEqual(self.card.ease_factor, 2.5)
        self.assertEqual(self.card.interval, 1)
        self.assertEqual(self.card.repetitions, 0)

    def test_spaced_repetition_algorithm(self):
        """Test the SM-2 spaced repetition algorithm"""
        # Test with good quality (3)
        next_review = self.card.get_next_review_date(3)
        self.assertEqual(self.card.repetitions, 1)
        self.assertEqual(self.card.interval, 1)
        
        # Test second repetition
        next_review = self.card.get_next_review_date(3)
        self.assertEqual(self.card.repetitions, 2)
        self.assertEqual(self.card.interval, 6)
        
        # Test poor quality (resets)
        next_review = self.card.get_next_review_date(1)
        self.assertEqual(self.card.repetitions, 0)
        self.assertEqual(self.card.interval, 1)

    def test_is_due_for_review(self):
        """Test if card is correctly identified as due for review"""
        # New card should be due
        self.assertTrue(self.card.is_due_for_review(self.user))
        
        # Create a study session in the future
        future_date = timezone.now() + timedelta(days=1)
        StudySession.objects.create(
            user=self.user,
            card=self.card,
            difficulty=3,
            next_review=future_date
        )
        
        # Card should not be due now
        self.assertFalse(self.card.is_due_for_review(self.user))


class StudySessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deck = Deck.objects.create(name='Test Deck', owner=self.user)
        self.card = Card.objects.create(
            deck=self.deck,
            question='Test Question',
            answer='Test Answer'
        )

    def test_study_session_creation(self):
        """Test study session creation and next review calculation"""
        session = StudySession.objects.create(
            user=self.user,
            card=self.card,
            difficulty=3,
            response_time=5.0
        )
        
        self.assertIsNotNone(session.next_review)
        self.assertEqual(session.response_time, 5.0)

    def test_get_due_cards(self):
        """Test getting due cards for a user"""
        # All cards should be due initially
        due_cards = StudySession.get_due_cards(self.user)
        self.assertIn(self.card, due_cards)
        
        # Create a future study session
        future_date = timezone.now() + timedelta(days=1)
        StudySession.objects.create(
            user=self.user,
            card=self.card,
            difficulty=3,
            next_review=future_date
        )
        
        # Card should not be in due cards now
        due_cards = StudySession.get_due_cards(self.user)
        self.assertNotIn(self.card, due_cards)


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = UserProfile.objects.create(user=self.user)

    def test_streak_update(self):
        """Test study streak calculation"""
        # First study
        self.profile.update_streak()
        self.assertEqual(self.profile.current_streak, 1)
        self.assertEqual(self.profile.longest_streak, 1)
        
        # Study again same day (shouldn't change streak)
        self.profile.update_streak()
        self.assertEqual(self.profile.current_streak, 1)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deck = Deck.objects.create(name='Test Deck', owner=self.user)
        self.card = Card.objects.create(
            deck=self.deck,
            question='Test Question',
            answer='Test Answer'
        )

    def test_home_page(self):
        """Test the main study page loads correctly"""
        response = self.client.get(reverse('cards'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Question')

    def test_api_cards_endpoint(self):
        """Test the cards API endpoint"""
        response = self.client.get(reverse('api_cards'))
        self.assertEqual(response.status_code, 200)
        
        # Check JSON response
        data = response.json()
        self.assertIsInstance(data, list)
        if data:  # If there are cards
            self.assertIn('id', data[0])
            self.assertIn('question', data[0])
            self.assertIn('answer', data[0])

    def test_study_session_api_requires_login(self):
        """Test that study session API requires authentication"""
        response = self.client.post(reverse('api_study_session'), {
            'card_id': self.card.id,
            'difficulty': 3,
            'response_time': 5.0
        }, content_type='application/json')
        
        # Should redirect to login or return 302/401
        self.assertIn(response.status_code, [302, 401, 403])

    def test_study_session_api_with_login(self):
        """Test study session API with authenticated user"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(reverse('api_study_session'), {
            'card_id': self.card.id,
            'difficulty': 3,
            'response_time': 5.0
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that study session was created
        self.assertTrue(StudySession.objects.filter(
            user=self.user,
            card=self.card
        ).exists())

    def test_statistics_page(self):
        """Test the statistics page"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('study_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Study Statistics')


class StudyNoteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deck = Deck.objects.create(name='Test Deck', owner=self.user)
        self.card = Card.objects.create(
            deck=self.deck,
            question='Test Question',
            answer='Test Answer'
        )

    def test_note_creation(self):
        """Test creating study notes"""
        note = StudyNote.objects.create(
            user=self.user,
            card=self.card,
            content='This is a test note'
        )
        
        self.assertEqual(note.content, 'This is a test note')
        self.assertEqual(note.user, self.user)
        self.assertEqual(note.card, self.card)

    def test_note_api_with_login(self):
        """Test notes API with authenticated user"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(reverse('api_save_note'), {
            'card_id': self.card.id,
            'content': 'API test note'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that note was created
        self.assertTrue(StudyNote.objects.filter(
            user=self.user,
            content='API test note'
        ).exists())


class IntegrationTest(TestCase):
    """Integration tests for the complete study workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deck = Deck.objects.create(name='Math', owner=self.user)
        
        # Create multiple cards
        self.cards = []
        for i in range(5):
            card = Card.objects.create(
                deck=self.deck,
                question=f'What is {i}+{i}?',
                answer=str(i*2)
            )
            self.cards.append(card)

    def test_complete_study_workflow(self):
        """Test a complete study session workflow"""
        self.client.login(username='testuser', password='testpass')
        
        # 1. Load the study page
        response = self.client.get(reverse('cards'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Study each card
        for card in self.cards:
            response = self.client.post(reverse('api_study_session'), {
                'card_id': card.id,
                'difficulty': 3,  # Good
                'response_time': 5.0
            }, content_type='application/json')
            self.assertEqual(response.status_code, 200)
        
        # 3. Check statistics
        response = self.client.get(reverse('study_statistics'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify user profile was updated
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.total_cards_studied, 5)
        self.assertGreater(profile.total_study_time, 0)

    def test_spaced_repetition_workflow(self):
        """Test that spaced repetition works correctly over time"""
        self.client.login(username='testuser', password='testpass')
        
        card = self.cards[0]
        
        # Study card with good difficulty
        response = self.client.post(reverse('api_study_session'), {
            'card_id': card.id,
            'difficulty': 4,  # Easy
            'response_time': 3.0
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that card is scheduled for future review
        session = StudySession.objects.get(user=self.user, card=card)
        self.assertGreater(session.next_review, timezone.now())
        
        # Verify card is not in due cards immediately
        due_cards = StudySession.get_due_cards(self.user)
        self.assertNotIn(card, due_cards)
