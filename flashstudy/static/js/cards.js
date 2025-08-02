/**
 * Flash Study Card System JavaScript
 * Handles card navigation, study sessions, and user interactions
 */

class CardStudySystem {
    constructor() {
        this.currentCardIndex = 0;
        this.cards = [];
        this.filteredCards = [];
        this.isAnswerVisible = false;
        this.studyStartTime = null;
        this.cardStartTime = null;
        this.sessionTimer = null;
        this.cardTimer = null;
        this.studySession = {
            cardsStudied: 0,
            totalTime: 0,
            correctAnswers: 0,
            startTime: null
        };

        this.init();
    }
    
    init() {
        this.loadCards();
        this.bindEvents();
        this.setupKeyboardShortcuts();
        this.setupSearch();
        this.setupFilters();
        this.startStudySession();
        this.showKeyboardHints();
    }
    
    loadCards() {
        // Get cards from the DOM
        const cardElements = document.querySelectorAll('.card-content[data-card-id]');
        this.cards = Array.from(cardElements).map(el => ({
            id: el.dataset.cardId,
            question: el.querySelector('h3').textContent,
            deck: el.querySelector('.card-deck').textContent,
            deckId: el.dataset.deck,
            element: el
        }));

        this.filteredCards = [...this.cards];

        // Load full card data via AJAX if needed
        this.loadCardDetails();
        this.updateCardCount();
    }
    
    async loadCardDetails() {
        try {
            const response = await fetch('/api/cards/');
            if (response.ok) {
                const cardData = await response.json();
                this.cards = this.cards.map(card => {
                    const fullData = cardData.find(c => c.id == card.id);
                    return fullData ? { ...card, ...fullData } : card;
                });
            }
        } catch (error) {
            console.log('Using DOM data for cards');
        }
    }
    
    bindEvents() {
        // Card selection from left panel
        document.querySelectorAll('.card-content[data-card-id]').forEach(card => {
            card.addEventListener('click', (e) => {
                const cardId = e.currentTarget.dataset.cardId;
                this.selectCard(cardId);
            });
        });
        
        // Answer reveal button
        const revealBtn = document.querySelector('.reveal-btn');
        if (revealBtn) {
            revealBtn.addEventListener('click', () => this.toggleAnswer());
        }
        
        // Difficulty buttons
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const difficulty = parseInt(e.target.dataset.difficulty);
                this.submitAnswer(difficulty);
            });
        });
        
        // Notes functionality
        const notesTextarea = document.querySelector('textarea');
        const saveNotesBtn = document.querySelector('button:not(.reveal-btn):not(.difficulty-btn)');
        
        if (saveNotesBtn && notesTextarea) {
            saveNotesBtn.addEventListener('click', () => this.saveNotes(notesTextarea.value));
        }

        // Navigation buttons
        const prevBtn = document.getElementById('prev-card');
        const nextBtn = document.getElementById('next-card');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousCard());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextCard());

        // Quick action buttons
        const markKnownBtn = document.getElementById('mark-known');
        const markDifficultBtn = document.getElementById('mark-difficult');
        const skipBtn = document.getElementById('skip-card');

        if (markKnownBtn) markKnownBtn.addEventListener('click', () => this.submitAnswer(4));
        if (markDifficultBtn) markDifficultBtn.addEventListener('click', () => this.submitAnswer(1));
        if (skipBtn) skipBtn.addEventListener('click', () => this.skipCard());

        // Queue controls
        const shuffleBtn = document.getElementById('shuffle-cards');
        const resetBtn = document.getElementById('reset-queue');

        if (shuffleBtn) shuffleBtn.addEventListener('click', () => this.shuffleCards());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetQueue());
    }

    setupSearch() {
        const searchInput = document.getElementById('card-search');
        const searchBtn = document.getElementById('search-btn');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterCards(e.target.value));
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.filterCards(e.target.value);
                }
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const query = searchInput ? searchInput.value : '';
                this.filterCards(query);
            });
        }
    }

    setupFilters() {
        const deckFilter = document.getElementById('deck-filter');

        if (deckFilter) {
            deckFilter.addEventListener('change', (e) => this.filterByDeck(e.target.value));
        }
    }

    filterCards(query) {
        const searchTerm = query.toLowerCase().trim();

        if (!searchTerm) {
            this.filteredCards = [...this.cards];
        } else {
            this.filteredCards = this.cards.filter(card =>
                card.question.toLowerCase().includes(searchTerm) ||
                card.deck.toLowerCase().includes(searchTerm)
            );
        }

        this.updateCardDisplay();
        this.updateCardCount();

        if (this.filteredCards.length > 0) {
            this.currentCardIndex = 0;
            this.displayCurrentCard();
        }
    }

    filterByDeck(deckId) {
        if (!deckId) {
            this.filteredCards = [...this.cards];
        } else {
            this.filteredCards = this.cards.filter(card => card.deckId === deckId);
        }

        this.updateCardDisplay();
        this.updateCardCount();

        if (this.filteredCards.length > 0) {
            this.currentCardIndex = 0;
            this.displayCurrentCard();
        }
    }

    updateCardDisplay() {
        const cardsList = document.getElementById('cards-list');
        if (!cardsList) return;

        // Hide all cards
        this.cards.forEach(card => {
            if (card.element) {
                card.element.style.display = 'none';
            }
        });

        // Show filtered cards
        this.filteredCards.forEach(card => {
            if (card.element) {
                card.element.style.display = 'block';
            }
        });
    }

    updateCardCount() {
        const countElement = document.getElementById('card-count');
        const totalCardsElement = document.getElementById('total-cards');

        if (countElement) {
            countElement.textContent = `(${this.filteredCards.length})`;
        }

        if (totalCardsElement) {
            totalCardsElement.textContent = this.filteredCards.length;
        }
    }

    shuffleCards() {
        // Fisher-Yates shuffle algorithm
        for (let i = this.filteredCards.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.filteredCards[i], this.filteredCards[j]] = [this.filteredCards[j], this.filteredCards[i]];
        }

        this.currentCardIndex = 0;
        this.updateCardDisplay();
        this.displayCurrentCard();
        this.showFeedback('Cards shuffled! 🔀');
    }

    resetQueue() {
        this.filteredCards = [...this.cards];
        this.currentCardIndex = 0;
        this.updateCardDisplay();
        this.updateCardCount();
        this.displayCurrentCard();

        // Reset search and filters
        const searchInput = document.getElementById('card-search');
        const deckFilter = document.getElementById('deck-filter');

        if (searchInput) searchInput.value = '';
        if (deckFilter) deckFilter.value = '';

        this.showFeedback('Queue reset! 🔄');
    }

    skipCard() {
        this.showFeedback('Card skipped ⏭️');
        setTimeout(() => this.nextCard(), 500);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Prevent shortcuts when typing in input fields
            if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;

            switch(e.key) {
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    this.toggleAnswer();
                    break;
                case '1':
                    e.preventDefault();
                    if (this.isAnswerVisible) this.submitAnswer(1);
                    break;
                case '2':
                    e.preventDefault();
                    if (this.isAnswerVisible) this.submitAnswer(2);
                    break;
                case '3':
                    e.preventDefault();
                    if (this.isAnswerVisible) this.submitAnswer(3);
                    break;
                case '4':
                    e.preventDefault();
                    if (this.isAnswerVisible) this.submitAnswer(4);
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousCard();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextCard();
                    break;
                case '?':
                    e.preventDefault();
                    this.toggleKeyboardHints();
                    break;
                case 's':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.saveCurrentNotes();
                    }
                    break;
            }
        });
    }

    toggleKeyboardHints() {
        const hints = document.getElementById('keyboard-hints');
        if (hints) {
            hints.classList.toggle('show');
        }
    }
    
    selectCard(cardId) {
        const cardIndex = this.cards.findIndex(card => card.id == cardId);
        if (cardIndex !== -1) {
            this.currentCardIndex = cardIndex;
            this.displayCurrentCard();
            this.startCardTimer();
        }
    }
    
    displayCurrentCard() {
        if (this.filteredCards.length === 0) return;

        const currentCard = this.filteredCards[this.currentCardIndex];
        const activeCardElement = document.getElementById('active-card');

        if (activeCardElement && currentCard) {
            // Add slide-out animation
            activeCardElement.classList.add('slide-out');

            setTimeout(() => {
                // Update card content
                activeCardElement.dataset.cardId = currentCard.id;

                const questionElement = document.getElementById('card-question');
                const answerElement = document.getElementById('card-answer-text');
                const deckBadge = document.querySelector('.card-deck-badge');

                if (questionElement) questionElement.textContent = currentCard.question;
                if (answerElement && currentCard.answer) {
                    answerElement.textContent = currentCard.answer;
                }
                if (deckBadge) deckBadge.textContent = currentCard.deck;

                // Reset answer visibility
                this.hideAnswer();

                // Update progress
                this.updateProgress();

                // Highlight current card in left panel
                this.highlightCurrentCard();

                // Add slide-in animation
                activeCardElement.classList.remove('slide-out');
                activeCardElement.classList.add('slide-in');

                setTimeout(() => {
                    activeCardElement.classList.remove('slide-in');
                }, 300);
            }, 150);
        }
    }

    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        const currentCardNum = document.getElementById('current-card-num');

        if (progressFill && this.filteredCards.length > 0) {
            const progress = ((this.currentCardIndex + 1) / this.filteredCards.length) * 100;
            progressFill.style.width = `${progress}%`;
        }

        if (currentCardNum) {
            currentCardNum.textContent = this.currentCardIndex + 1;
        }
    }
    
    highlightCurrentCard() {
        // Remove previous highlights
        document.querySelectorAll('.card-content[data-card-id]').forEach(el => {
            el.classList.remove('current-card');
        });
        
        // Highlight current card
        const currentCard = this.cards[this.currentCardIndex];
        if (currentCard && currentCard.element) {
            currentCard.element.classList.add('current-card');
        }
    }
    
    toggleAnswer() {
        const answerDiv = document.getElementById('card-answer');
        const revealBtn = document.querySelector('.reveal-btn');
        
        if (!answerDiv || !revealBtn) return;
        
        if (this.isAnswerVisible) {
            this.hideAnswer();
        } else {
            this.showAnswer();
        }
    }
    
    showAnswer() {
        const answerDiv = document.getElementById('card-answer');
        const revealBtn = document.querySelector('.reveal-btn');
        
        answerDiv.style.display = 'block';
        answerDiv.style.opacity = '0';
        
        setTimeout(() => {
            answerDiv.style.opacity = '1';
        }, 50);
        
        revealBtn.textContent = 'Hide Answer';
        this.isAnswerVisible = true;
        
        // Show difficulty buttons
        document.querySelector('.study-controls').style.display = 'block';
    }
    
    hideAnswer() {
        const answerDiv = document.getElementById('card-answer');
        const revealBtn = document.querySelector('.reveal-btn');
        
        answerDiv.style.display = 'none';
        revealBtn.textContent = 'Show Answer';
        this.isAnswerVisible = false;
        
        // Hide difficulty buttons
        document.querySelector('.study-controls').style.display = 'none';
    }
    
    async submitAnswer(difficulty) {
        if (!this.isAnswerVisible) return;

        const currentCard = this.filteredCards[this.currentCardIndex];
        const responseTime = this.getCardResponseTime();

        // Update study session stats
        this.studySession.cardsStudied++;
        if (difficulty >= 3) {
            this.studySession.correctAnswers++;
        }

        // Update session display
        this.updateSessionStats();

        // Submit to backend
        try {
            await this.saveStudySession(currentCard.id, difficulty, responseTime);
        } catch (error) {
            console.error('Failed to save study session:', error);
            this.showFeedback('Failed to save progress', 'error');
        }

        // Provide visual feedback
        this.showAnswerFeedback(difficulty);

        // Clear notes for next card
        const notesTextarea = document.getElementById('study-notes');
        if (notesTextarea) {
            notesTextarea.value = '';
        }

        // Move to next card after delay
        setTimeout(() => {
            this.nextCard();
        }, 1000);
    }
    
    async saveStudySession(cardId, difficulty, responseTime) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        const response = await fetch('/api/study-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                card_id: cardId,
                difficulty: difficulty,
                response_time: responseTime
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save study session');
        }
        
        return response.json();
    }
    
    showAnswerFeedback(difficulty) {
        const feedbackMessages = {
            1: { text: 'Keep practicing!', color: '#e74c3c' },
            2: { text: 'Getting better!', color: '#f39c12' },
            3: { text: 'Good job!', color: '#27ae60' },
            4: { text: 'Excellent!', color: '#2ecc71' }
        };
        
        const feedback = feedbackMessages[difficulty];
        const activeCard = document.getElementById('active-card');
        
        // Create feedback element
        const feedbackEl = document.createElement('div');
        feedbackEl.className = 'answer-feedback';
        feedbackEl.textContent = feedback.text;
        feedbackEl.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: ${feedback.color};
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        activeCard.style.position = 'relative';
        activeCard.appendChild(feedbackEl);
        
        // Animate feedback
        setTimeout(() => feedbackEl.style.opacity = '1', 50);
        setTimeout(() => {
            feedbackEl.style.opacity = '0';
            setTimeout(() => feedbackEl.remove(), 300);
        }, 700);
    }
    
    nextCard() {
        if (this.filteredCards.length === 0) return;

        if (this.currentCardIndex < this.filteredCards.length - 1) {
            this.currentCardIndex++;
        } else {
            this.currentCardIndex = 0; // Loop back to first card
            this.showFeedback('Reached end of deck, starting over! 🔄');
        }
        this.displayCurrentCard();
        this.startCardTimer();
    }

    previousCard() {
        if (this.filteredCards.length === 0) return;

        if (this.currentCardIndex > 0) {
            this.currentCardIndex--;
        } else {
            this.currentCardIndex = this.filteredCards.length - 1; // Loop to last card
        }
        this.displayCurrentCard();
        this.startCardTimer();
    }

    saveCurrentNotes() {
        const notesTextarea = document.getElementById('study-notes');
        if (notesTextarea && notesTextarea.value.trim()) {
            this.saveNotes(notesTextarea.value);
        }
    }
    
    startStudySession() {
        this.studyStartTime = Date.now();
        this.studySession.startTime = Date.now();
        this.startCardTimer();
        this.startSessionTimer();
    }

    startCardTimer() {
        this.cardStartTime = Date.now();

        // Clear existing timer
        if (this.cardTimer) {
            clearInterval(this.cardTimer);
        }

        // Start card timer display
        this.cardTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.cardStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;

            const timerElement = document.getElementById('card-timer');
            if (timerElement) {
                timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    startSessionTimer() {
        // Clear existing timer
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
        }

        // Start session timer display
        this.sessionTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.studySession.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;

            const sessionTimeElement = document.getElementById('session-time');
            if (sessionTimeElement) {
                sessionTimeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    getCardResponseTime() {
        return this.cardStartTime ? (Date.now() - this.cardStartTime) / 1000 : 0;
    }

    updateSessionStats() {
        const sessionCardsElement = document.getElementById('session-cards');
        const sessionCorrectElement = document.getElementById('session-correct');
        const sessionAccuracyElement = document.getElementById('session-accuracy');

        if (sessionCardsElement) {
            sessionCardsElement.textContent = this.studySession.cardsStudied;
        }

        if (sessionCorrectElement) {
            sessionCorrectElement.textContent = this.studySession.correctAnswers;
        }

        if (sessionAccuracyElement) {
            const accuracy = this.studySession.cardsStudied > 0
                ? Math.round((this.studySession.correctAnswers / this.studySession.cardsStudied) * 100)
                : 0;
            sessionAccuracyElement.textContent = `${accuracy}%`;
        }
    }

    showFeedback(message, type = 'info') {
        // Create or update feedback element
        let feedbackEl = document.getElementById('feedback-message');

        if (!feedbackEl) {
            feedbackEl = document.createElement('div');
            feedbackEl.id = 'feedback-message';
            feedbackEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s ease;
                max-width: 300px;
            `;
            document.body.appendChild(feedbackEl);
        }

        // Set background color based on type
        const colors = {
            info: '#667eea',
            success: '#27ae60',
            warning: '#f39c12',
            error: '#e74c3c'
        };

        feedbackEl.style.background = colors[type] || colors.info;
        feedbackEl.textContent = message;
        feedbackEl.style.opacity = '1';

        // Auto-hide after 3 seconds
        setTimeout(() => {
            feedbackEl.style.opacity = '0';
        }, 3000);
    }

    showKeyboardHints() {
        const hintsHtml = `
            <div class="keyboard-hints" id="keyboard-hints">
                <h4>Keyboard Shortcuts</h4>
                <div><kbd>Space</kbd> / <kbd>Enter</kbd> - Show/Hide Answer</div>
                <div><kbd>1</kbd> - Again</div>
                <div><kbd>2</kbd> - Hard</div>
                <div><kbd>3</kbd> - Good</div>
                <div><kbd>4</kbd> - Easy</div>
                <div><kbd>←</kbd> / <kbd>→</kbd> - Navigate Cards</div>
                <div><kbd>?</kbd> - Toggle This Help</div>
            </div>
        `;

        if (!document.getElementById('keyboard-hints')) {
            document.body.insertAdjacentHTML('beforeend', hintsHtml);

            // Show hints briefly on load
            setTimeout(() => {
                const hints = document.getElementById('keyboard-hints');
                if (hints) {
                    hints.classList.add('show');
                    setTimeout(() => hints.classList.remove('show'), 5000);
                }
            }, 1000);
        }
    }
    
    async saveNotes(content) {
        if (!content.trim()) return;
        
        const currentCard = this.cards[this.currentCardIndex];
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        try {
            const response = await fetch('/api/notes/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    card_id: currentCard?.id,
                    content: content
                })
            });
            
            if (response.ok) {
                // Show success feedback
                const textarea = document.querySelector('textarea');
                const originalPlaceholder = textarea.placeholder;
                textarea.placeholder = 'Note saved!';
                textarea.value = '';
                
                setTimeout(() => {
                    textarea.placeholder = originalPlaceholder;
                }, 2000);
            }
        } catch (error) {
            console.error('Failed to save note:', error);
        }
    }
}

// Initialize the card system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.card-area')) {
        window.cardSystem = new CardStudySystem();
    }
});

// Add CSS for current card highlighting and feedback
const style = document.createElement('style');
style.textContent = `
    .card-content.current-card {
        border: 2px solid #667eea !important;
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
    }
    
    .study-controls {
        display: none;
    }
    
    .answer-feedback {
        animation: feedbackPulse 0.6s ease-in-out;
    }
    
    @keyframes feedbackPulse {
        0% { transform: translate(-50%, -50%) scale(0.8); }
        50% { transform: translate(-50%, -50%) scale(1.1); }
        100% { transform: translate(-50%, -50%) scale(1); }
    }
`;
document.head.appendChild(style);
