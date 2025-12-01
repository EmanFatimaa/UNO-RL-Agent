# Game logic (cards, rules, deck)

"""
UNO Game Logic - Handles all game rules, cards, and game flow
No AI or graphics here, just pure game mechanics
"""

import random
from enum import Enum

class Color(Enum):
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    WILD = 4

class CardType(Enum):
    NUMBER = 0
    SKIP = 1
    REVERSE = 2
    DRAW_TWO = 3
    WILD = 4
    WILD_DRAW_FOUR = 5

class Card:
    """Represents a single UNO card"""
    def __init__(self, color, card_type, number=None):
        self.color = color
        self.card_type = card_type
        self.number = number
    
    def __repr__(self):
        if self.card_type == CardType.NUMBER:
            return f"{self.color.name} {self.number}"
        return f"{self.color.name} {self.card_type.name}"
    
    def can_play_on(self, other_card, current_color):
        """Check if this card can legally be played on another card"""
        # Wild cards can always be played
        if self.color == Color.WILD:
            return True
        # Same color as current color
        if self.color == current_color:
            return True
        # Number cards match by number
        if self.card_type == CardType.NUMBER and other_card.card_type == CardType.NUMBER:
            return self.number == other_card.number
        # Action cards match by type
        if self.card_type == other_card.card_type and self.card_type != CardType.NUMBER:
            return True
        return False
    
    def get_color_rgb(self):
        """Get RGB color for rendering"""
        color_map = {
            Color.RED: (220, 20, 60),
            Color.BLUE: (30, 144, 255),
            Color.GREEN: (50, 205, 50),
            Color.YELLOW: (255, 215, 0),
            Color.WILD: (50, 50, 50)
        }
        return color_map[self.color]


class UnoGame:
    """Main game class - manages the entire UNO game state"""
    
    def __init__(self):
        self.reset()
    
    def create_deck(self):
        """Create a standard 108-card UNO deck"""
        deck = []
        # Number cards (0 once, 1-9 twice per color)
        for color in [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]:
            deck.append(Card(color, CardType.NUMBER, 0))
            for num in range(1, 10):
                deck.extend([Card(color, CardType.NUMBER, num)] * 2)
            # Action cards (2 of each per color)
            for _ in range(2):
                deck.append(Card(color, CardType.SKIP, None))
                deck.append(Card(color, CardType.REVERSE, None))
                deck.append(Card(color, CardType.DRAW_TWO, None))
        # Wild cards (4 of each)
        for _ in range(4):
            deck.append(Card(Color.WILD, CardType.WILD, None))
            deck.append(Card(Color.WILD, CardType.WILD_DRAW_FOUR, None))
        return deck
    
    def reset(self):
        """Reset game to initial state"""
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        
        # Deal 7 cards to each player (0=human, 1=AI)
        self.player_hand = [self.deck.pop() for _ in range(7)]
        self.ai_hand = [self.deck.pop() for _ in range(7)]
        
        # Start discard pile with a number card
        while True:
            start_card = self.deck.pop()
            if start_card.card_type == CardType.NUMBER:
                self.discard_pile = [start_card]
                break
        
        self.current_color = self.discard_pile[0].color
        self.current_player = 0  # 0 = player, 1 = AI
        self.game_over = False
        self.winner = None
        self.message = "Your turn! Click a card or draw."
    
    def get_top_card(self):
        """Get the top card of discard pile"""
        return self.discard_pile[-1]
    
    def get_valid_cards(self, hand):
        """Get indices of cards that can be played from a hand"""
        top_card = self.get_top_card()
        valid_indices = []
        for i, card in enumerate(hand):
            if card.can_play_on(top_card, self.current_color):
                valid_indices.append(i)
        return valid_indices
    
    def draw_card(self, player):
        """Draw a card for a player (0=human, 1=AI)"""
        if len(self.deck) == 0:
            # Reshuffle discard pile if deck is empty
            if len(self.discard_pile) > 1:
                top_card = self.discard_pile.pop()
                self.deck = self.discard_pile
                random.shuffle(self.deck)
                self.discard_pile = [top_card]
            else:
                return None  # No cards left
        
        card = self.deck.pop()
        if player == 0:
            self.player_hand.append(card)
        else:
            self.ai_hand.append(card)
        return card
    
    def play_card(self, player, card_index, chosen_color=None):
        """
        Play a card from player's hand
        Returns True if successful, False if invalid move
        """
        hand = self.player_hand if player == 0 else self.ai_hand
        
        # Validate card index
        if card_index < 0 or card_index >= len(hand):
            return False
        
        card = hand[card_index]
        top_card = self.get_top_card()
        
        # Check if card can be played
        if not card.can_play_on(top_card, self.current_color):
            return False
        
        # Play the card
        played_card = hand.pop(card_index)
        self.discard_pile.append(played_card)
        
        # Handle wild cards - need to choose color
        if played_card.color == Color.WILD:
            if chosen_color:
                self.current_color = chosen_color
            else:
                # Default: choose most common color in hand
                self.current_color = self.choose_color_for_wild(hand)
        else:
            self.current_color = played_card.color
        
        # Check for win condition
        if len(hand) == 0:
            self.game_over = True
            self.winner = player
            self.message = "You win!" if player == 0 else "AI wins!"
        
        return True
    
    def choose_color_for_wild(self, hand):
        """Smart color choice for wild cards - pick most common color"""
        color_counts = {Color.RED: 0, Color.BLUE: 0, Color.GREEN: 0, Color.YELLOW: 0}
        for card in hand:
            if card.color in color_counts:
                color_counts[card.color] += 1
        
        # Return most common color, or random if empty hand
        if max(color_counts.values()) > 0:
            return max(color_counts, key=color_counts.get)
        return random.choice([Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW])
    
    def switch_turn(self):
        """Switch to next player"""
        self.current_player = 1 - self.current_player
        if self.current_player == 0:
            self.message = "Your turn!"
        else:
            self.message = "AI is thinking..."
    
    def get_state_for_ai(self):
        """
        Convert game state to format the AI can understand
        Returns a dictionary with all relevant information
        """
        return {
            'hand': self.ai_hand.copy(),
            'top_card': self.get_top_card(),
            'current_color': self.current_color,
            'player_card_count': len(self.player_hand),
            'deck_size': len(self.deck)
        }