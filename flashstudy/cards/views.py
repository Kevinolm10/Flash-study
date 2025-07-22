from django.shortcuts import render
from .models import Card, Deck
from django.core.paginator import Paginator

def homePage(request):
    # Get all cards or cards from a specific deck
    cards = Card.objects.all()
    paginator = Paginator(cards, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'cards.html', context)
