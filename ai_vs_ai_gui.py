# ai_vs_ai_gui.py
import pygame, sys, time
from multiplayer_game import MultiplayerGame
from ql_agent import RandomAgent, HeuristicAgent, QLearningAgent
from uno_game import Color, CardType

pygame.init()

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
FPS = 30

WHITE=(255,255,255); BLACK=(0,0,0); GREEN=(34,139,34)
CARD_WIDTH = 55
CARD_HEIGHT = 90
CARD_RADIUS = 8

class AIVsAIGUI:
    def __init__(self, num_players=2, move_delay=0.5):
        assert 2 <= num_players <= 4
        self.num_players = num_players
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI vs AI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small = pygame.font.Font(None, 16)

        self.game = MultiplayerGame(num_players)
        # assign simple agents; you may replace some slots with QLearningAgent() loaded models
        self.agents = []
        for i in range(num_players):
            # alternate simple heuristics to make games interesting
            if i % 3 == 0:
                self.agents.append(RandomAgent())
            else:
                self.agents.append(HeuristicAgent())

        self.move_delay = int(move_delay * 1000)  # milliseconds
        self.last_move_time = pygame.time.get_ticks()

        # layout helpers
        self.top_y = 30
        self.bottom_y = WINDOW_HEIGHT - CARD_HEIGHT - 120

    def draw_card(self, card, x, y):
        pygame.draw.rect(self.screen, WHITE, (x,y,CARD_WIDTH,CARD_HEIGHT), border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, (x,y,CARD_WIDTH,CARD_HEIGHT), width=2, border_radius=CARD_RADIUS)
        inner = card.get_color_rgb()
        pygame.draw.rect(self.screen, inner, (x+6, y+8, CARD_WIDTH-12, CARD_HEIGHT-16), border_radius=6)
        if card.card_type == CardType.NUMBER:
            text = str(card.number)
        else:
            mapping = {CardType.SKIP:"Skip", CardType.REVERSE:"Rev", CardType.DRAW_TWO:"+2",
                       CardType.WILD:"Wild", CardType.WILD_DRAW_FOUR:"+4"}
            text = mapping.get(card.card_type,"?")
        txt = self.font.render(text, True, WHITE)
        self.screen.blit(txt, (x + CARD_WIDTH//2 - txt.get_width()//2, y + CARD_HEIGHT//2 - txt.get_height()//2))

    def compute_positions(self, player_index, count):
        # simple 2x2 corner layout like multiplayer GUI
        n = len(self.game.hands[player_index])
        if player_index == 0:
            y = self.top_y; start_x = 30
        elif player_index == 1:
            y = self.top_y; start_x = WINDOW_WIDTH - (min(10, n) * (CARD_WIDTH+6)) - 30
        elif player_index == 2:
            y = self.bottom_y; start_x = 30
        else:
            y = self.bottom_y; start_x = WINDOW_WIDTH - (min(10, n) * (CARD_WIDTH+6)) - 30

        spacing = min(CARD_WIDTH+6, max(20, (WINDOW_WIDTH//2 - 80)//max(1, n-1)))
        return start_x, y, spacing

    def draw(self):
        self.screen.fill(GREEN)
        # draw top text
        top = self.game.get_top_card()
        txt = self.font.render(f"Top: {top}", True, WHITE)
        self.screen.blit(txt, (20, 20))
        # draw hands (all face-up)
        for p in range(self.num_players):
            start_x, y, spacing = self.compute_positions(p, self.num_players)
            for i, card in enumerate(self.game.hands[p]):
                x = start_x + i * spacing
                self.draw_card(card, x, y)
            lbl = self.small.render(f"P{p+1} ({len(self.game.hands[p])})", True, WHITE)
            self.screen.blit(lbl, (start_x, y - 18))
        # turn indicator
        turn = self.font.render(f"P{self.game.current_player+1}'s turn", True, (255,255,0))
        self.screen.blit(turn, (WINDOW_WIDTH - 200, 20))

        pygame.display.flip()

    def step_ai(self):
        cp = self.game.current_player
        state = self.game.get_state_for_ai(cp)
        valid = self.game.get_valid_cards(cp)
        if valid:
            action = self.agents[cp].choose_action(state, valid)
            card = self.game.hands[cp][action]
            if card.color == Color.WILD:
                chosen = self.game.choose_color_for_wild(cp)
                self.game.play_card(cp, action, chosen)
            else:
                self.game.play_card(cp, action)
        else:
            if self.game.pending_draw > 0:
                self.game.draw_multiple_cards(cp, self.game.pending_draw)
                self.game.pending_draw = 0
            else:
                self.game.draw_card(cp)
        if not self.game.game_over:
            self.game.switch_turn()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

            now = pygame.time.get_ticks()
            # do a move every move_delay ms
            if now - self.last_move_time >= self.move_delay and not self.game.game_over:
                self.step_ai()
                self.last_move_time = now

            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    AIVsAIGUI(num_players=2, move_delay=0.5).run()
