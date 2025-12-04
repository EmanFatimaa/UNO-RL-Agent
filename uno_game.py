""" 
Game logic (cards, rules, deck)
UNO Game Logic - Handles all game rules, cards, and game flow
No AI logic or graphics here, just pure game mechanics

Features:
- Full UNO deck creation (108 cards)
- Correct handling for Draw Two / Wild Draw Four stacking
- Skip and Reverse behavior (Reverse acts like skip in 2-player)
- Wild color selection (auto-choose most common color in hand)
- Reshuffle discard pile into deck when deck is exhausted
"""

import random
from enum import Enum 

# --- Enums to model card properties ---

class Color(Enum):
    """Color enum for UNO cards. WILD is used for wild cards (no color)."""
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    WILD = 4

class CardType(Enum):
    """Types of UNO cards. NUMBER uses 'number' field. Action cards ignore number."""
    NUMBER = 0
    SKIP = 1
    REVERSE = 2
    DRAW_TWO = 3
    WILD = 4
    WILD_DRAW_FOUR = 5

# --- Card representation ---
class Card:
    """Represents a single UNO card.

    Attributes:
        color (Color): Color enum. Color.WILD for wild cards.
        card_type (CardType): Type of the card (NUMBER, SKIP, etc.)
        number (int|None): For NUMBER type cards, stores the numeric value (0-9).
    """
    def __init__(self, color, card_type, number=None):
        # Validate inputs
        self.color = color
        self.card_type = card_type
        self.number = number
    
    def __repr__(self):
        # String representation for debugging
        if self.card_type == CardType.NUMBER: 
            return f"{self.color.name} {self.number}"
        return f"{self.color.name} {self.card_type.name}"
    
    def __eq__(self, other):
        # Equality check for cards
        if not isinstance(other, Card):
            return False
        return (self.color == other.color and 
                self.card_type == other.card_type and 
                self.number == other.number)
    
    def __hash__(self):
        # Hash for using cards in sets/dicts
        return hash((self.color, self.card_type, self.number))
    
    def can_play_on(self, other_card, current_color):
        """
        Check if this card can legally be played on top of other_card
        given the current_color in effect.

        Rules implemented:
        - Wild cards (color WILD) can always be played.
        - If this card's color matches current_color, it's playable.
        - If both this card and other_card are NUMBER and numbers match, it's playable.
        - If this card and other_card share the same action type (e.g., both SKIP),
          it's playable (action-card matching).
        """
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
        # Otherwise not playable
        return False
    
    def get_color_rgb(self):
        """Return an RGB tuple suitable for rendering card UI (not used by game logic)."""
        color_map = {
            Color.RED: (220, 20, 60),
            Color.BLUE: (30, 144, 255),
            Color.GREEN: (50, 205, 50),
            Color.YELLOW: (255, 215, 0),
            Color.WILD: (50, 50, 50)
        }
        return color_map[self.color]
    
    def get_strategic_value(self):
        """
        Heuristic value for AI to evaluate card usefulness.
        Higher = stronger effect/value.

        This is arbitrary and intended for simple AI heuristics:
        - Wild Draw Four: 10
        - Wild: 8
        - Draw Two: 7
        - Skip: 6
        - Reverse: 5
        - Number: returns its numeric value or 3 as default.
        """
        if self.card_type == CardType.WILD_DRAW_FOUR:
            return 10
        elif self.card_type == CardType.WILD:
            return 8
        elif self.card_type == CardType.DRAW_TWO:
            return 7
        elif self.card_type == CardType.SKIP:
            return 6
        elif self.card_type == CardType.REVERSE:
            return 5
        else:
            return self.number if self.number is not None else 3

# --- Main UnoGame class (game engine) ---
class UnoGame:
    """Main game class with with rules for all the cards.

    Intended for 2-player games: player (0) vs AI (1).
    """
    
    def __init__(self):
        # direction: 1 = clockwise (player -> ai -> player ...),
        # -1 = counter-clockwise.
        # In 2-player games direction flips still, but reverse is treated like skip.
        self.direction = 1

        # pending_draw: number of cards the next player must pick up unless they stack
        # with a Draw Two or Wild Draw Four.
        self.pending_draw = 0

        # skip_next: whether the upcoming player's turn should be skipped.
        self.skip_next = False  # Flag for skip card

        # discard_history: chronological list of cards played 
        self.discard_history = []

        # turns_played: counts how many card-play turns have occurred
        self.turns_played = 0

         # last_action_cards: rolling window of recent action cards 
        self.last_action_cards = []

         # Initialize/reset the game to a starting state
        self.reset()
    
    def create_deck(self):
        """
        Create the standard 108-card UNO deck.

        Composition:
        - For each color (RED/BLUE/GREEN/YELLOW):
            - 1 x 0
            - 2 x (1..9)
            - 2 x SKIP
            - 2 x REVERSE
            - 2 x DRAW_TWO
        - 4 x WILD
        - 4 x WILD_DRAW_FOUR"""

        deck = []

        # Add colored cards
        for color in [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]:

            # One zero per color
            deck.append(Card(color, CardType.NUMBER, 0))

            # Two of each number 1-9 per color
            for num in range(1, 10):
                deck.extend([Card(color, CardType.NUMBER, num)] * 2)

            # Two of each action card per color
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
        """Reset the entire game to an initial state:
        - rebuild and shuffle deck
        - deal 7 cards to each player
        - set an initial top-of-discard as a number card
        - reset flags and counters
        """
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        
        # Deal 7 cards to each player: player_hand (0) and ai_hand (1)
        self.player_hand = [self.deck.pop() for _ in range(7)]
        self.ai_hand = [self.deck.pop() for _ in range(7)]
        
        # the first discard/top card is a number card (many UNO rules forbid starting
        # on an action card). If we pop an action/wild, keep popping until we find a number.
        while True:
            start_card = self.deck.pop()
            if start_card.card_type == CardType.NUMBER:
                self.discard_pile = [start_card]
                break
        
        self.current_color = self.discard_pile[0].color  # Current color is the color of the starting card
        self.current_player = 0  # 0 = player, 1 = AI

         # Reset state variables
        self.direction = 1
        self.pending_draw = 0
        self.skip_next = False
        self.game_over = False
        self.winner = None

        # Message for UI / logs
        self.message = "Your turn! Click a card or draw."

        # History and tracking variables
        self.discard_history = [start_card]
        self.turns_played = 0
        self.last_action_cards = []
    
    # ---- Helper Functions ----
    def get_top_card(self):
        """Get the top card of discard pile"""
        return self.discard_pile[-1]
    
    def get_valid_cards(self, hand):
        """
        Return a list of indices (into `hand`) that can be legally played given the
        current top card and current_color.

        Special case: if pending_draw > 0, only Draw Two and Wild Draw Four may be played
        to stack the penalty.
        """
        top_card = self.get_top_card()
        valid_indices = []
        
        # If there's a pending draw, only allow stacking with DRAW_TWO or WILD_DRAW_FOUR
        if self.pending_draw > 0:
            for i, card in enumerate(hand):
                if card.card_type in [CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR]:
                    valid_indices.append(i)
            return valid_indices
        
         # Normal play - any card that matches top card by rules (color / number / action-type)
        for i, card in enumerate(hand):
            if card.can_play_on(top_card, self.current_color):
                valid_indices.append(i)
        return valid_indices
    
    def get_recent_colors(self, n=5):
        """
        Return the last n non-wild colors played (useful for AI heuristics).
        If there are fewer than n entries, return what is available.
        """
        recent = self.discard_history[-n:] if len(self.discard_history) >= n else self.discard_history
        # Filter out wild cards (wild has no color preference)
        return [card.color for card in recent if card.color != Color.WILD]
    
     # ---- Drawing logic ----
    def draw_card(self, player):
        """
        Draw a single card for player:
            player == 0 -> player's hand
            player == 1 -> ai_hand

        If deck is empty, reshuffle discard pile (except top card) into the deck.
        Returns: the drawn Card object or None if no cards available.
        """

        if len(self.deck) == 0:
            # Reshuffle discard pile if deck is empty
            if len(self.discard_pile) > 1:
                top_card = self.discard_pile.pop()# keep the top card visible
                self.deck = self.discard_pile # take the rest into deck
                random.shuffle(self.deck)
                self.discard_pile = [top_card] # reset discard pile with top card
            else:
                return None  # No cards left
        
        card = self.deck.pop()
        if player == 0:
            self.player_hand.append(card)
        else:
            self.ai_hand.append(card)
        return card
    
    def draw_multiple_cards(self, player, count):
        """Draw count cards for player. Returns list of drawn Card objects."""
        drawn_cards = []
        for _ in range(count):
            card = self.draw_card(player)
            if card:
                drawn_cards.append(card)
        return drawn_cards
    
    def play_card(self, player, card_index, chosen_color=None):
        """
        Play a card from the chosen player's hand.

        Parameters:
            player (int): 0 for human player, 1 for AI
            card_index (int): index within the player's hand to play
            chosen_color (Color, optional): For wild cards, the desired color.

        Returns:
            True if the play was successful; False if the play was invalid.
        """
        # Get the correct hand
        hand = self.player_hand if player == 0 else self.ai_hand
        
        # Validate card index
        if card_index < 0 or card_index >= len(hand):
            return False
        
        card = hand[card_index]
        top_card = self.get_top_card()

        # Enforce play legality:
        # - If pending draw > 0, only allow Draw Two or Wild Draw Four to stack
        # - Otherwise rely on Card.can_play_on rules
        # Check if card can be played
        if not card.can_play_on(top_card, self.current_color):
            # If there's a pending draw, only Draw Two/Four allowed
            if self.pending_draw > 0:
                if card.card_type not in [CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR]:
                    return False
            else:
                return False
        
        # Play the card
        played_card = hand.pop(card_index)
        self.discard_pile.append(played_card)
        self.discard_history.append(played_card)
        self.turns_played += 1
        
        # Track action cards
        if played_card.card_type in [CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO, 
                                     CardType.WILD, CardType.WILD_DRAW_FOUR]:
            self.last_action_cards.append(played_card)
            if len(self.last_action_cards) > 5:
                self.last_action_cards.pop(0)
        
        # Handle wild cards - need to choose color
        if played_card.color == Color.WILD:
            if chosen_color:
                self.current_color = chosen_color
            else:
                # Default: choose most common color in hand
                self.current_color = self.choose_color_for_wild(hand)
        else:
            self.current_color = played_card.color
        
        # *** CORRECTED ACTION CARD EFFECTS ***
        
        # DRAW TWO - opponent must draw 2 cards
        if played_card.card_type == CardType.DRAW_TWO:
            self.pending_draw += 2
            self.message = f"Player {player} played Draw Two! +2 cards pending!"
        
        # WILD DRAW FOUR - opponent must draw 4 cards
        elif played_card.card_type == CardType.WILD_DRAW_FOUR:
            self.pending_draw += 4
            self.message = f"Player {player} played Wild Draw Four! +4 cards pending!"
        
        # SKIP - opponent's turn is skipped
        elif played_card.card_type == CardType.SKIP:
            self.skip_next = True
            self.message = f"Player {player} played Skip! Next player skipped!"
        
        # REVERSE - reverse direction (in 2-player, acts like skip)
        elif played_card.card_type == CardType.REVERSE:
            self.direction *= -1
            # In 2-player game, reverse = skip
            self.skip_next = True
            self.message = f"Player {player} played Reverse!"
        
        # Check for win condition
        if len(hand) == 0:
            self.game_over = True
            self.winner = player
            self.message = "You win!" if player == 0 else "AI wins!"
        
        return True
    
    def handle_turn_start(self, player):
        """
        Handle pending effects at start of turn
        Returns True if player can play normally, False if turn is affected
        """
        # Handle pending draw cards
        if self.pending_draw > 0:
            opponent = 1 - player
            # Check if current player can counter with Draw Two/Four
            valid_counters = [i for i, card in enumerate(
                self.player_hand if player == 0 else self.ai_hand
            ) if card.card_type in [CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR]]
            
            if not valid_counters:
                # Must draw the cards
                drawn = self.draw_multiple_cards(player, self.pending_draw)
                self.message = f"Player {player} draws {self.pending_draw} cards!"
                self.pending_draw = 0
                # Turn ends after drawing
                return False
        
        # Handle skip
        if self.skip_next:
            self.skip_next = False
            self.message = f"Player {player}'s turn is skipped!"
            return False
        
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
        """Switch to next player with proper turn flow"""
        self.current_player = 1 - self.current_player
        
        # Check if new player's turn is affected by action cards
        can_play = self.handle_turn_start(self.current_player)
        
        # If turn was skipped/forced to draw, switch again
        if not can_play and not self.game_over:
            self.current_player = 1 - self.current_player
        
        if self.current_player == 0:
            self.message = "Your turn!"
        else:
            self.message = "AI is thinking..."
    
    def get_hand_stats(self, hand):
        """Get detailed statistics about a hand"""
        stats = {
            'total_cards': len(hand),
            'color_counts': {Color.RED: 0, Color.BLUE: 0, Color.GREEN: 0, Color.YELLOW: 0, Color.WILD: 0},
            'has_wild': False,
            'has_wild_draw_four': False,
            'has_draw_two': False,
            'has_skip': False,
            'has_reverse': False,
            'action_card_count': 0,
            'total_value': 0
        }
        
        for card in hand:
            stats['color_counts'][card.color] += 1
            
            if card.card_type == CardType.WILD:
                stats['has_wild'] = True
            elif card.card_type == CardType.WILD_DRAW_FOUR:
                stats['has_wild_draw_four'] = True
            elif card.card_type == CardType.DRAW_TWO:
                stats['has_draw_two'] = True
            elif card.card_type == CardType.SKIP:
                stats['has_skip'] = True
            elif card.card_type == CardType.REVERSE:
                stats['has_reverse'] = True
            
            if card.card_type != CardType.NUMBER:
                stats['action_card_count'] += 1
            
            stats['total_value'] += card.get_strategic_value()
        
        return stats
    
    def get_state_for_ai(self, perspective_player=1):
        """
        Enhanced state representation with action card tracking
        """
        my_hand = self.ai_hand if perspective_player == 1 else self.player_hand
        opponent_hand = self.player_hand if perspective_player == 1 else self.ai_hand
        
        my_stats = self.get_hand_stats(my_hand)
        
        return {
            'hand': my_hand.copy(),
            'top_card': self.get_top_card(),
            'current_color': self.current_color,
            'opponent_card_count': len(opponent_hand),
            'deck_size': len(self.deck),
            'my_card_count': len(my_hand),
            'hand_stats': my_stats,
            'recent_colors': self.get_recent_colors(3),
            'turns_played': self.turns_played,
            'game_progress': self.turns_played / 50.0,
            'pending_draw': self.pending_draw,  # NEW: Important for strategy
            'skip_next': self.skip_next,  # NEW: Know if next turn is skipped
            'direction': self.direction  # NEW: Turn direction
        }