# This file creates the visual multiplayer version of UNO (2–4 players).
# It connects the Pygame GUI to your MultiplayerGame logic.

import pygame, sys, time
from multiplayer_game import MultiplayerGame
from uno_game import Color, CardType

pygame.init()

# compact card size you requested
CARD_WIDTH = 55
CARD_HEIGHT = 90
CARD_RADIUS = 8

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
FPS = 60

WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (34,139,34)
DARK = (20,20,20)
YELLOW = (255,215,0)
RED = (220,50,50)

class MultiplayerGUI:
    def __init__(self, num_players=2):
        assert 2 <= num_players <= 4
        self.num_players = num_players
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"UNO - Multiplayer ({num_players})")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small = pygame.font.Font(None, 18)

        self.game = MultiplayerGame(num_players)
        self.selected_card = None
        self.choosing_color = False
        self.notification = ""
        self.notification_t = 0

        # corner positions
        self.padding = 20
        self.top_y = 30
        self.bottom_y = WINDOW_HEIGHT - CARD_HEIGHT - 120
        self.left_x = 30
        self.right_x = WINDOW_WIDTH - (CARD_WIDTH * 6) - 60  # reserve space for up to 6 cards

        # center discard
        self.discard_center = (WINDOW_WIDTH//2 - CARD_WIDTH//2, WINDOW_HEIGHT//2 - CARD_HEIGHT//2)

        # deck rect (left of discard)
        self.deck_rect = pygame.Rect(self.discard_center[0] - CARD_WIDTH - 40, self.discard_center[1], CARD_WIDTH, CARD_HEIGHT)

    def show_notification(self, txt, dur=120):
        self.notification = txt
        self.notification_t = dur

    def draw_card(self, card, x, y, face_up=True):
        # card outer
        pygame.draw.rect(self.screen, WHITE if face_up else (180,180,180), (x, y, CARD_WIDTH, CARD_HEIGHT), border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), width=2, border_radius=CARD_RADIUS)
        if face_up:
            inner = card.get_color_rgb()
            pygame.draw.rect(self.screen, inner, (x+6, y+8, CARD_WIDTH-12, CARD_HEIGHT-16), border_radius=6)
            if card.card_type == CardType.NUMBER:
                text = str(card.number)
            else:
                mapping = {CardType.SKIP:"Skip", CardType.REVERSE:"Rev", CardType.DRAW_TWO:"+2",
                           CardType.WILD:"Wild", CardType.WILD_DRAW_FOUR:"+4"}
                text = mapping.get(card.card_type, "?")
            txt = self.font.render(text, True, WHITE)
            self.screen.blit(txt, (x + CARD_WIDTH//2 - txt.get_width()//2, y + CARD_HEIGHT//2 - txt.get_height()//2))

    def compute_hand_layout(self, player_index):
        # determine corner coordinates and compute spacing that fits
        hand = self.game.hands[player_index]
        n = len(hand)
        # max cards to reserve visually is 12; spacing will shrink to fit
        max_space = 6 * CARD_WIDTH
        # compute available width per corner
        half_width = WINDOW_WIDTH // 2 - 80
        if player_index in (0, 2):  # left corners
            base_x = self.left_x
        else:  # right corners
            base_x = self.right_x + (WINDOW_WIDTH//2 - (self.right_x + 60))
        if player_index in (0,1):  # top row
            y = self.top_y
        else:
            y = self.bottom_y

        # compute spacing: we want cards to be horizontal block centered in the corner area
        max_allowed = min(half_width - 40, 6 * CARD_WIDTH)
        if n <= 1:
            spacing = CARD_WIDTH + 10
            total_width = CARD_WIDTH
        else:
            spacing = min(CARD_WIDTH + 12, max(20, (max_allowed - CARD_WIDTH) // (n - 1)))
            total_width = CARD_WIDTH + (n - 1) * spacing

        # compute starting x per quadrant
        if player_index == 0:  # top-left
            start_x = 40
        elif player_index == 1:  # top-right
            start_x = WINDOW_WIDTH - total_width - 40
        elif player_index == 2:  # bottom-left
            start_x = 40
        else:  # bottom-right
            start_x = WINDOW_WIDTH - total_width - 40

        return start_x, y, spacing

    def handle_click(self, mx, my):
        # clicking a card for the current player only
        cur = self.game.current_player
        # compute rects for cur player's hand
        start_x, y, spacing = self.compute_hand_layout(cur)
        rects = []
        for i in range(len(self.game.hands[cur])):
            x = start_x + i * spacing
            rects.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        for i, r in enumerate(rects):
            if r.collidepoint((mx,my)):
                card = self.game.hands[cur][i]
                # if playable
                if card.can_play_on(self.game.get_top_card(), self.game.current_color):
                    if card.color == Color.WILD:
                        chosen = self.game.choose_color_for_wild(cur)
                        self.game.play_card(cur, i, chosen)
                        self.show_notification(f"P{cur+1} played {card} -> {chosen.name}", 90)
                    else:
                        self.game.play_card(cur, i)
                        self.show_notification(f"P{cur+1} played {card}", 90)
                    # after play switch turn (engine handles skip/pending_draw)
                    if not self.game.game_over:
                        self.game.switch_turn()
                else:
                    # invalid play: if no valid cards allow draw
                    valid = self.game.get_valid_cards(cur)
                    if not valid:
                        drawn = self.game.draw_card(cur)
                        if drawn and drawn.can_play_on(self.game.get_top_card(), self.game.current_color):
                            # auto-play drawn card
                            if drawn.color == Color.WILD:
                                chosen = self.game.choose_color_for_wild(cur)
                                self.game.play_card(cur, len(self.game.hands[cur]) - 1, chosen)
                                self.show_notification(f"P{cur+1} drew and played {drawn}", 90)
                            else:
                                self.game.play_card(cur, len(self.game.hands[cur]) - 1)
                                self.show_notification(f"P{cur+1} drew and played {drawn}", 90)
                        else:
                            self.show_notification("Drew a card; turn ends", 60)
                            self.game.switch_turn()
                    else:
                        self.show_notification("Invalid card!", 60)
                return

        # deck clicked
        if self.deck_rect.collidepoint((mx,my)):
            cur = self.game.current_player
            if self.game.pending_draw > 0:
                self.game.draw_multiple_cards(cur, self.game.pending_draw)
                self.game.pending_draw = 0
                self.show_notification(f"P{cur+1} drew stacked cards", 90)
                self.game.switch_turn()
            else:
                drawn = self.game.draw_card(cur)
                if drawn and drawn.can_play_on(self.game.get_top_card(), self.game.current_color):
                    # auto-play drawn card
                    if drawn.color == Color.WILD:
                        chosen = self.game.choose_color_for_wild(cur)
                        self.game.play_card(cur, len(self.game.hands[cur]) - 1, chosen)
                    else:
                        self.game.play_card(cur, len(self.game.hands[cur]) - 1)
                    self.show_notification("You drew a playable card - auto-played", 80)
                    if not self.game.game_over:
                        self.game.switch_turn()
                else:
                    self.show_notification("Drew a card; turn ends", 60)
                    self.game.switch_turn()

    def draw(self):
        self.screen.fill(GREEN)

        # draw discard center
        top = self.game.get_top_card()
        dx, dy = self.discard_center
        self.draw_card(top, dx, dy, face_up=True)
        # deck pile (left)
        pygame.draw.rect(self.screen, (40,40,40), self.deck_rect, border_radius=8)
        deck_txt = self.small.render(f"{len(self.game.deck)}", True, WHITE)
        self.screen.blit(deck_txt, (self.deck_rect.x + 6, self.deck_rect.y + CARD_HEIGHT + 6))

        # draw each player's hand in corner
        for p in range(self.num_players):
            if p >= self.num_players:
                continue
            start_x, y, spacing = self.compute_hand_layout(p)
            hand = self.game.hands[p]
            for i, card in enumerate(hand):
                x = start_x + i * spacing
                self.draw_card(card, x, y, face_up=True)
            # player label and count
            lbl = f"P{p+1} ({len(hand)})"
            label_surf = self.font.render(lbl, True, WHITE)
            if p in (0,2):  # left side: put label under or above
                if p in (0,1):
                    self.screen.blit(label_surf, (start_x, y - 22))
                else:
                    self.screen.blit(label_surf, (start_x, y + CARD_HEIGHT + 8))
            else:
                if p in (0,1):
                    self.screen.blit(label_surf, (start_x, y - 22))
                else:
                    self.screen.blit(label_surf, (start_x, y + CARD_HEIGHT + 8))

        # turn indicator top center
        turn_txt = self.font.render(f"P{self.game.current_player + 1}'s turn", True, YELLOW)
        self.screen.blit(turn_txt, (WINDOW_WIDTH//2 - turn_txt.get_width()//2, 8))

        # notifications
        if self.notification_t > 0:
            n = self.small.render(self.notification, True, BLACK)
            box = pygame.Rect(WINDOW_WIDTH//2 - n.get_width()//2 - 10, 60, n.get_width()+20, 28)
            pygame.draw.rect(self.screen, WHITE, box, border_radius=6)
            pygame.draw.rect(self.screen, BLACK, box, width=2, border_radius=6)
            self.screen.blit(n, (box.x+10, box.y+5))
            self.notification_t -= 1

        # game over overlay
        if self.game.game_over:
            ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            ov.set_alpha(200)
            ov.fill((0,0,0))
            self.screen.blit(ov, (0,0))
            winner = self.game.winner
            txt = self.font.render(f"Player {winner+1} wins!", True, (255,255,255))
            self.screen.blit(txt, (WINDOW_WIDTH//2 - txt.get_width()//2, WINDOW_HEIGHT//2 - 20))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mx,my = pygame.mouse.get_pos()
                    # only allow clicks when it's a human player's turn
                    self.handle_click(mx,my)
            # draw
            self.draw()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    MultiplayerGUI(num_players=4).run()
