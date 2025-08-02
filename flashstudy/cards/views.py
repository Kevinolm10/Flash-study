from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User
import json
from .models import Card, Deck, StudySession, UserProfile, StudyNote

def homePage(request):
    """Main study page with cards for studying"""
    # Get cards due for review if user is authenticated
    if request.user.is_authenticated:
        cards = StudySession.get_due_cards(request.user)[:20]  # Limit to 20 cards

        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Update streak if studying today
        if cards.exists():
            profile.update_streak()
    else:
        cards = Card.objects.all()[:20]  # Show all cards for anonymous users
        profile = None

    # Get all decks for filtering
    decks = Deck.objects.all().order_by('name')

    context = {
        'cards': cards,
        'profile': profile,
        'decks': decks,
    }
    return render(request, 'cards.html', context)


@require_http_methods(["GET"])
def api_cards(request):
    """API endpoint to get cards data as JSON"""
    if request.user.is_authenticated:
        cards = StudySession.get_due_cards(request.user)[:20]
    else:
        cards = Card.objects.all()[:20]

    cards_data = []
    for card in cards:
        cards_data.append({
            'id': card.id,
            'question': card.question,
            'answer': card.answer,
            'deck': card.deck.name,
            'ease_factor': card.ease_factor,
            'interval': card.interval,
            'repetitions': card.repetitions,
        })

    return JsonResponse(cards_data, safe=False)


@login_required
@require_http_methods(["POST"])
def api_study_session(request):
    """API endpoint to save study session data"""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        difficulty = data.get('difficulty')
        response_time = data.get('response_time', 0)

        card = get_object_or_404(Card, id=card_id)

        # Create study session
        session = StudySession.objects.create(
            user=request.user,
            card=card,
            difficulty=difficulty,
            response_time=response_time
        )

        # Update user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.total_cards_studied += 1
        profile.total_study_time += response_time / 60  # Convert to minutes
        profile.save()

        return JsonResponse({
            'success': True,
            'next_review': session.next_review.isoformat(),
            'message': 'Study session saved successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def api_save_note(request):
    """API endpoint to save study notes"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        card_id = data.get('card_id')

        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Note content cannot be empty'
            }, status=400)

        card = None
        if card_id:
            card = get_object_or_404(Card, id=card_id)

        note = StudyNote.objects.create(
            user=request.user,
            card=card,
            content=content
        )

        return JsonResponse({
            'success': True,
            'note_id': note.id,
            'message': 'Note saved successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def study_statistics(request):
    """View for displaying user study statistics"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Get recent study sessions
    recent_sessions = StudySession.objects.filter(user=request.user).order_by('-studied_at')[:10]

    # Calculate statistics
    total_sessions = StudySession.objects.filter(user=request.user).count()
    avg_response_time = StudySession.objects.filter(user=request.user).aggregate(
        avg_time=Avg('response_time')
    )['avg_time'] or 0

    # Difficulty distribution
    difficulty_stats = StudySession.objects.filter(user=request.user).values('difficulty').annotate(
        count=Count('difficulty')
    ).order_by('difficulty')

    context = {
        'profile': profile,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'avg_response_time': round(avg_response_time, 2),
        'difficulty_stats': difficulty_stats,
    }

    return render(request, 'study_statistics.html', context)


def deck_view(request, deck_id):
    """View cards from a specific deck"""
    deck = get_object_or_404(Deck, id=deck_id)

    if request.user.is_authenticated:
        # Get due cards from this deck
        cards = StudySession.get_due_cards(request.user, deck=deck)
    else:
        cards = deck.cards.all()

    context = {
        'cards': cards,
        'deck': deck,
    }

    return render(request, 'cards.html', context)
