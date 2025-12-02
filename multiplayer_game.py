# multiplayer_game.py
import random
from collections import deque
from uno_game import Color, CardType, Card  # reuse Card, Color, CardType

class MultiplayerGame:
    """
    Minimal N-player UNO engine (2-4 players).
    - hands: list of lists of Card
    - current_player: index 0..n-1
    - direction: 1 or -1
    - pending_draw: stacked draw penalty
    - skip_next: boolean (skips the immediate next player)
    """

    def __init__(self, num_players=2):
        assert 2 <= num_players <= 4, "Supported players: 2-4"
        self.num_players = num_players
        self.direction = 1
        self.pending_draw = 0
        self.skip_next = False
        self.turns_played = 0
        self.discard_history = []
        self.last_action_cards = []
        self.reset()

    def create_deck(self):
        deck = []
        for color in [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]:
            deck.append(Card(color, CardType.NUMBER, 0))
            for num in range(1, 10):
                deck.extend([Card(color, CardType.NUMBER, num)] * 2)
            for _ in range(2):
                deck.append(Card(color, CardType.SKIP, None))
                deck.append(Card(color, CardType.REVERSE, None))
                deck.append(Card(color, CardType.DRAW_TWO, None))
        for _ in range(4):
            deck.append(Card(Color.WILD, CardType.WILD, None))
            deck.append(Card(Color.WILD, CardType.WILD_DRAW_FOUR, None))
        return deck

    def reset(self):
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.hands = [[self.deck.pop() for _ in range(7)] for _ in range(self.num_players)]
        # start discard with a number
        while True:
            c = self.deck.pop()
            if c.card_type == CardType.NUMBER:
                self.discard_pile = [c]
                break
            else:
                # place non-number into deck bottom
                self.deck.insert(0, c)
        self.current_color = self.discard_pile[0].color
        self.current_player = 0
        self.direction = 1
        self.pending_draw = 0
        self.skip_next = False
        self.game_over = False
        self.winner = None
        self.turns_played = 0
        self.discard_history = [self.discard_pile[0]]
        self.last_action_cards = []

    def get_top_card(self):
        return self.discard_pile[-1]

    def draw_card(self, player):
        if len(self.deck) == 0:
            if len(self.discard_pile) > 1:
                top = self.discard_pile.pop()
                self.deck = self.discard_pile[:]
                random.shuffle(self.deck)
                self.discard_pile = [top]
            else:
                return None
        card = self.deck.pop()
        self.hands[player].append(card)
        return card

    def draw_multiple_cards(self, player, count):
        drawn = []
        for _ in range(count):
            c = self.draw_card(player)
            if c:
                drawn.append(c)
        return drawn

    def get_valid_cards(self, hand_index):
        hand = self.hands[hand_index]
        top = self.get_top_card()
        valid = []
        if self.pending_draw > 0:
            for i, c in enumerate(hand):
                if c.card_type in (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR):
                    valid.append(i)
            return valid
        for i, c in enumerate(hand):
            if c.color == Color.WILD:
                valid.append(i)
            elif c.color == self.current_color:
                valid.append(i)
            elif c.card_type == CardType.NUMBER and top.card_type == CardType.NUMBER and c.number == top.number:
                valid.append(i)
            elif c.card_type == top.card_type and c.card_type != CardType.NUMBER:
                valid.append(i)
        return valid

    def choose_color_for_wild(self, hand_index):
        counts = {Color.RED:0, Color.BLUE:0, Color.GREEN:0, Color.YELLOW:0}
        for c in self.hands[hand_index]:
            if c.color in counts:
                counts[c.color] += 1
        if max(counts.values()) == 0:
            return random.choice([Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW])
        return max(counts, key=counts.get)

    def play_card(self, player, card_index, chosen_color=None):
        if self.game_over:
            return False
        hand = self.hands[player]
        if card_index < 0 or card_index >= len(hand):
            return False
        card = hand[card_index]
        top = self.get_top_card()
        if not card.can_play_on(top, self.current_color):
            if self.pending_draw > 0 and card.card_type not in (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR):
                return False
            if self.pending_draw == 0:
                return False
        played = hand.pop(card_index)
        self.discard_pile.append(played)
        self.discard_history.append(played)
        self.turns_played += 1
        if played.card_type in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO, CardType.WILD, CardType.WILD_DRAW_FOUR):
            self.last_action_cards.append(played)
            if len(self.last_action_cards) > 8:
                self.last_action_cards.pop(0)
        # handle wild color
        if played.color == Color.WILD:
            if chosen_color:
                self.current_color = chosen_color
            else:
                self.current_color = self.choose_color_for_wild(player)
        else:
            self.current_color = played.color

        # apply effects
        if played.card_type == CardType.DRAW_TWO:
            self.pending_draw += 2
        elif played.card_type == CardType.WILD_DRAW_FOUR:
            self.pending_draw += 4
        elif played.card_type == CardType.SKIP:
            self.skip_next = True
        elif played.card_type == CardType.REVERSE:
            self.direction *= -1
            # in 2-player reverse acts like skip, but in N-player it flips direction
            if self.num_players == 2:
                self.skip_next = True

        # check win
        if len(hand) == 0:
            self.game_over = True
            self.winner = player
        return True

    def handle_turn_start(self, player):
        # pending draw
        if self.pending_draw > 0:
            # can counter?
            hand = self.hands[player]
            counters = [i for i,c in enumerate(hand) if c.card_type in (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR)]
            if not counters:
                self.draw_multiple_cards(player, self.pending_draw)
                self.pending_draw = 0
                return False
        if self.skip_next:
            self.skip_next = False
            return False
        return True

    def switch_turn(self):
        # step forward respecting direction and skip logic handled elsewhere
        self.current_player = (self.current_player + self.direction) % self.num_players
        # handle automatic start-of-turn effects
        can = self.handle_turn_start(self.current_player)
        if not can:
            # if turn ended due to drawing pending, move to next
            self.current_player = (self.current_player + self.direction) % self.num_players

    def get_hand(self, player):
        return list(self.hands[player])

    def get_state_for_ai(self, perspective_player=0):
        return {
            'hand': self.get_hand(perspective_player),
            'top_card': self.get_top_card(),
            'current_color': self.current_color,
            'opponent_counts': [len(self.hands[i]) for i in range(self.num_players) if i != perspective_player],
            'my_card_count': len(self.hands[perspective_player]),
            'deck_size': len(self.deck),
            'pending_draw': self.pending_draw,
            'direction': self.direction,
            'turns_played': self.turns_played
        }
