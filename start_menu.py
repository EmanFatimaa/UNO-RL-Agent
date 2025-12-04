# This file creates the main menu screen for your UNO project using Pygame.
#lets the player choose what type of UNO game to play: Human vs AI, AI vs AI, or Multiplayer and then it loads the correct game module.

import pygame
import sys

# Import game modes
from gui import UnoGUI                      # Player vs AI (your existing GUI)
from ai_vs_ai_gui import AIVsAIGUI         # AI vs AI mode
from multiplayer_gui import MultiplayerGUI # Multiplayer 2–4 players

pygame.init()

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (34,139,34)
BLUE = (70,130,180)
ORANGE = (255,140,0)
RED = (200,50,50)

class StartMenu:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("UNO - Select Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 30)

        # Buttons
        self.btn_player_vs_ai = pygame.Rect(WINDOW_WIDTH//2 - 150, 200, 300, 60)
        self.btn_ai_vs_ai = pygame.Rect(WINDOW_WIDTH//2 - 150, 290, 300, 60)
        self.btn_multiplayer = pygame.Rect(WINDOW_WIDTH//2 - 150, 380, 300, 60)

    def draw_button(self, rect, text, color):
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, rect, width=3, border_radius=10)
        txt = self.font.render(text, True, WHITE)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2,
                               rect.centery - txt.get_height()//2))

    def ask_player_count(self):
        """Popup selection for 2–4 players (for multiplayer mode)."""
        selecting = True
        count_buttons = [
            (pygame.Rect(WINDOW_WIDTH//2 - 160, 250, 90, 50), 2),
            (pygame.Rect(WINDOW_WIDTH//2 - 45, 250, 90, 50), 3),
            (pygame.Rect(WINDOW_WIDTH//2 + 70, 250, 90, 50), 4),
        ]

        while selecting:
            self.screen.fill(GREEN)

            title = self.font.render("Select number of players", True, WHITE)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 150))

            for rect, num in count_buttons:
                pygame.draw.rect(self.screen, BLUE, rect, border_radius=8)
                pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=8)
                txt = self.font.render(str(num), True, WHITE)
                self.screen.blit(txt, (rect.centerx - txt.get_width()//2,
                                       rect.centery - txt.get_height()//2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for rect, num in count_buttons:
                        if rect.collidepoint((mx,my)):
                            return num

            self.clock.tick(60)

    def run(self):
        running = True
        while running:
            self.screen.fill(GREEN)

            title = self.font.render("UNO - Select Game Mode", True, WHITE)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

            # Draw buttons
            self.draw_button(self.btn_player_vs_ai, "Human vs AI", BLUE)
            self.draw_button(self.btn_ai_vs_ai,   "AI vs AI", ORANGE)
            self.draw_button(self.btn_multiplayer, "Multiplayer", RED)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    # PLAYER VS AI — run your existing UNO GUI
                    if self.btn_player_vs_ai.collidepoint((mx,my)):
                        game = UnoGUI()
                        game.run()

                    # AI VS AI — run NPC-npc battle
                    if self.btn_ai_vs_ai.collidepoint((mx,my)):
                        game = AIVsAIGUI(num_players=2, base_move_delay=0.5)
                        game.run()

                    # MULTIPLAYER — ask player count then start
                    if self.btn_multiplayer.collidepoint((mx,my)):
                        num = self.ask_player_count()
                        game = MultiplayerGUI(num_players=num)
                        game.run()

            self.clock.tick(60)


if __name__ == "__main__":
    StartMenu().run()