from django.shortcuts import render
from .models import Card, Deck

def homePage(request):
    # Get all cards or cards from a specific deck
    cards = Card.objects.all()  # or filter by deck if needed
    
    context = {
        'cards': cards,
    }
    return render(request, 'cards.html', context)