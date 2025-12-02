# ai_vs_ai_gui.py
# Updated AI vs AI GUI for UNO
# - Back button returns to StartMenu (import & run)
# - Slower speeds (0.1x, 0.25x, 0.5x, 1.0x, 2.0x)
# - UNO rule enforcement (must "say UNO" on second-last -> else +2 penalty)
# - Removed playable-card highlighting
# - Fixed button alignment and layout
# - Detailed comments & explanations, including "white box" meaning
#
# NOTE: This file assumes these modules exist and expose the used methods:
#   - multiplayer_game.MultiplayerGame
#   - ql_agent.RandomAgent, HeuristicAgent, QLearningAgent
#   - uno_game.Color, CardType
#
# If your implementations use different method names/attributes, you may need
# small adjustments (comments point where those would be needed).

import pygame
import sys
import random
import time

# Local project imports (must exist in your project)
from multiplayer_game import MultiplayerGame
from ql_agent import RandomAgent, HeuristicAgent, QLearningAgent
from uno_game import Color, CardType

# Initialize pygame modules
pygame.init()

# -------------------- Window & appearance constants --------------------
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 30

# Colors (same palette as your main GUI for visual consistency)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (147, 112, 219)
CYAN = (0, 255, 255)

# Card drawing size & rounding (match other UI)
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_RADIUS = 10

# -------------------- GUI class --------------------
class AIVsAIGUI:
    """
    AI vs AI GUI class.
    Features:
      - Runs MultiplayerGame (AI players only)
      - Speed control with slow options (0.1x & 0.25x)
      - Back button returns to StartMenu by importing it and calling StartMenu().run()
      - UNO enforcement (GUI-level): if AI reaches 1 card and "forgets" UNO, they draw 2 if caught
      - No automatic playable-card highlighting (global toggle set to False)
      - Plenty of comments to explain each section and step
    """

    def __init__(self, num_players=2, base_move_delay=0.5):
        """
        Args:
            num_players (int): 2 - 4 players supported
            base_move_delay (float): the base unit delay in seconds for speed=1.0.
                                     e.g., base_move_delay=0.5 means 1.0x => 0.5s between moves.
        """
        assert 2 <= num_players <= 4
        self.num_players = num_players

        # Pygame window and fonts
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("UNO - AI vs AI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)

        # Game engine object (holds hands, deck, current_player, etc.)
        self.game = MultiplayerGame(num_players)

        # Create agents for each player. You can change agent types here.
        self.agents = []
        self.agent_names = []
        for i in range(num_players):
            if i == 0:
                # Q-Learning agent as player 1
                agent = QLearningAgent(name=f"Q-Agent-{i+1}")
                try:
                    agent.load_model()
                except Exception:
                    # If load fails, it's non-fatal — agent should still function
                    pass
                self.agent_names.append("Q-Learning")
            elif i % 2 == 0:
                agent = HeuristicAgent()
                self.agent_names.append("Heuristic")
            else:
                agent = RandomAgent()
                self.agent_names.append("Random")
            self.agents.append(agent)

        # ---- Timing / speed ----
        # base unit (ms) for speed 1.0
        self.base_delay_unit_ms = int(base_move_delay * 1000)
        # available speed multipliers (includes slower than 0.5 as requested)
        self.speeds = [0.1, 0.25, 0.5, 1.0, 2.0]
        self.game_speed = 0.5  # default start speed (you can change)
        self.move_delay = max(10, int(self.base_delay_unit_ms / self.game_speed))
        self.last_move_time = pygame.time.get_ticks()

        # ---- UI toggles ----
        # Remove playable-card highlight by default as requested
        self.enable_highlight = False

        # ---- Notifications & action effects ----
        self.notification = ""
        self.notification_timer = 0
        self.notification_color = WHITE

        self.action_effect = ""
        self.action_effect_timer = 0

        # ---- Buttons: top bar layout (aligned & consistent) ----
        top_y = 18
        btn_w = 140
        btn_h = 44
        gap = 12
        # Back button (top-left)
        self.back_button_rect = pygame.Rect(20, top_y, 120, 40)
        # End game (center-left)
        self.end_game_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_w - gap, top_y, btn_w, btn_h)
        # New game (center-right)
        self.new_game_button_rect = pygame.Rect(WINDOW_WIDTH // 2 + gap, top_y, btn_w, btn_h)
        # Speed (top-right)
        self.speed_button_rect = pygame.Rect(WINDOW_WIDTH - btn_w - 20, top_y, btn_w, btn_h)

        # Stats rectangle (right area)
        self.stats_rect = pygame.Rect(WINDOW_WIDTH - 280, 130, 260, 220)

        # Deck/discard center-left area rectangle (for convenient reference)
        self.deck_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - CARD_WIDTH - 120,
            WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2,
            CARD_WIDTH, CARD_HEIGHT
        )

        # ---- UNO rule GUI-level state ----
        # Track whether player has called UNO (True/False)
        self.uno_called = {i: False for i in range(num_players)}
        # Track when player reached 1 card (ms timestamp) to allow catch window
        self.uno_time = {i: None for i in range(num_players)}
        # How long (ms) other players have to catch a missed UNO
        self.uno_catch_window_ms = 1500  # 1.5 seconds
        # Probability an AI will "remember" to call UNO automatically
        self.ai_uno_call_prob = 0.98  # high by default; reduce to see more misses
        # How long notifications about UNO penalty last
        self.uno_penalty_message_duration = 120

    # -------------------- Small UI helpers --------------------
    def show_notification(self, message, color=WHITE, duration=120):
        """Display a centered notification for `duration` frames."""
        self.notification = message
        self.notification_color = color
        self.notification_timer = duration

    def show_action_effect(self, message, duration=180):
        """Display a small action effect message near bottom center."""
        self.action_effect = message
        self.action_effect_timer = duration

    # -------------------- Drawing helpers --------------------
    def draw_card(self, card, x, y, face_up=True, highlight=False):
        """
        Draw a single card.
        - If `face_up` is False we draw a gray back.
        - Highlighting is disabled globally with self.enable_highlight.
        """
        color = WHITE if face_up else GRAY

        # Only draw highlight if both requested and enabled
        if highlight and self.enable_highlight:
            pygame.draw.rect(self.screen, ORANGE,
                             (x - 4, y - 4, CARD_WIDTH + 8, CARD_HEIGHT + 8),
                             border_radius=CARD_RADIUS)

        pygame.draw.rect(self.screen, color, (x, y, CARD_WIDTH, CARD_HEIGHT),
                         border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT),
                         width=2, border_radius=CARD_RADIUS)

        if face_up:
            # Small inner rectangle colored according to card color for easy identification
            card_color = card.get_color_rgb()
            pygame.draw.rect(self.screen, card_color,
                             (x + 10, y + 10, CARD_WIDTH - 20, CARD_HEIGHT - 20),
                             border_radius=5)

            # Card center text (number or action)
            if card.card_type == CardType.NUMBER:
                text = str(card.number)
            else:
                mapping = {
                    CardType.SKIP: "Skip",
                    CardType.REVERSE: "Rev",
                    CardType.DRAW_TWO: "+2",
                    CardType.WILD: "Wild",
                    CardType.WILD_DRAW_FOUR: "+4"
                }
                text = mapping.get(card.card_type, "?")
            text_surface = self.font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
            self.screen.blit(text_surface, text_rect)

    def draw_player_hand(self, player_index, y_pos, face_up=True):
        """
        Draw the player's hand centered horizontally.
        Note: For AI vs AI we show all hands face-up for observation.
        """
        hand = self.game.hands[player_index]
        if len(hand) == 0:
            return

        spacing = 90
        total_width = max(len(hand) * spacing, CARD_WIDTH)
        start_x = (WINDOW_WIDTH - total_width) // 2

        for i, card in enumerate(hand):
            x = start_x + i * spacing
            # highlight flag set to False intentionally (no highlighting)
            self.draw_card(card, x, y_pos, face_up=face_up, highlight=False)

    def draw_discard_pile(self):
        """
        Draws:
          - Deck (face-down visual)
          - Central UNO circle
          - Deck count
          - Top-of-discard (face-up)
          - White info box (current color and pending draw)
        Explanation of the white box (explicit):
          - The white rounded rectangle below the discard shows the CURRENT ACTIVE COLOR
            (this is important after a Wild or Wild Draw Four). It helps viewers know
            which color is currently in play.
          - Beneath it, a red rounded box appears when there's a pending draw penalty
            (accumulated +2 / +4) indicating how many cards the next player must draw.
        """
        top_card = self.game.get_top_card()
        x = WINDOW_WIDTH // 2 - CARD_WIDTH - 20
        y = WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2

        # Draw deck (face-down) on the left of the discard area
        deck_color = (50, 50, 50)
        pygame.draw.rect(self.screen, deck_color,
                         (x - 100, y, CARD_WIDTH, CARD_HEIGHT),
                         border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK,
                         (x - 100, y, CARD_WIDTH, CARD_HEIGHT),
                         width=3, border_radius=CARD_RADIUS)

        # Decorative UNO circle on deck (spectator cue)
        center_x = x - 100 + CARD_WIDTH // 2
        center_y = y + CARD_HEIGHT // 2
        pygame.draw.circle(self.screen, (220, 20, 60), (center_x, center_y), 28)
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 28, 2)
        uno_text = self.small_font.render("UNO", True, WHITE)
        uno_rect = uno_text.get_rect(center=(center_x, center_y))
        self.screen.blit(uno_text, uno_rect)

        # Deck count label
        deck_count = self.tiny_font.render(f"{len(self.game.deck)} cards", True, WHITE)
        self.screen.blit(deck_count, (x - 95, y + CARD_HEIGHT + 5))

        # Draw the top card (face-up)
        self.draw_card(top_card, x + 20, y, face_up=True)

        # White info box: shows the current active color
        info_y = y + CARD_HEIGHT + 30
        color_bg = pygame.Rect(x - 10, info_y, 180, 30)
        pygame.draw.rect(self.screen, WHITE, color_bg, border_radius=6)
        pygame.draw.rect(self.screen, BLACK, color_bg, width=2, border_radius=6)
        color_name = getattr(self.game.current_color, "name", str(self.game.current_color))
        color_text = self.small_font.render(f"Color: {color_name}", True, BLACK)
        self.screen.blit(color_text, (x, info_y + 5))

        # Pending draw indicator (if present) — shows accumulated +2/+4 penalties
        pending_draw = getattr(self.game, "pending_draw", 0)
        if pending_draw > 0:
            pending_bg = pygame.Rect(x - 10, info_y + 40, 180, 30)
            pygame.draw.rect(self.screen, RED, pending_bg, border_radius=6)
            pygame.draw.rect(self.screen, BLACK, pending_bg, width=2, border_radius=6)
            pending_text = self.small_font.render(f"+{pending_draw} PENDING!", True, WHITE)
            self.screen.blit(pending_text, (x, info_y + 45))

    def draw_button(self, rect, text, color=DARK_GREEN, enabled=True):
        """Draws a rounded button with either one or two lines of text centered."""
        btn_color = color if enabled else GRAY
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=6)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=6)

        lines = text.split('\n')
        if len(lines) == 1:
            text_surface = self.small_font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
        else:
            # center multi-line text slightly shifted upwards
            for i, line in enumerate(lines):
                text_surface = self.tiny_font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery - 8 + i * 18))
                self.screen.blit(text_surface, text_rect)

    def draw_stats(self):
        """Draws right-side stats box containing turns and player card counts."""
        pygame.draw.rect(self.screen, WHITE, self.stats_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, self.stats_rect, width=2, border_radius=8)

        stats_lines = [
            "Game Stats:",
            f"Turns: {self.game.turns_played}",
            "",
            "Players:"
        ]

        for i in range(self.num_players):
            stats_lines.append(f"P{i+1}: {len(self.game.hands[i])} cards")
            stats_lines.append(f"  ({self.agent_names[i]})")

        for i, line in enumerate(stats_lines):
            text = self.tiny_font.render(line, True, BLACK)
            self.screen.blit(text, (self.stats_rect.x + 10, self.stats_rect.y + 8 + i * 18))

    def draw_notification(self):
        """Center-top notification box with countdown (frame-based)."""
        if self.notification_timer > 0:
            text_surface = self.font.render(self.notification, True, BLACK)
            text_rect = text_surface.get_rect()

            box_width = text_rect.width + 40
            box_height = text_rect.height + 20
            box_x = (WINDOW_WIDTH - box_width) // 2
            box_y = WINDOW_HEIGHT // 2 - 200

            bg_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(self.screen, self.notification_color, bg_rect, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, bg_rect, width=3, border_radius=10)

            text_rect.center = (WINDOW_WIDTH // 2, box_y + box_height // 2)
            self.screen.blit(text_surface, text_rect)
            self.notification_timer -= 1

    def draw_action_effect(self):
        """Small action effect (e.g., +2 played) near bottom center with countdown."""
        if self.action_effect_timer > 0:
            text_surface = self.small_font.render(self.action_effect, True, WHITE)
            text_rect = text_surface.get_rect()

            box_width = text_rect.width + 30
            box_height = text_rect.height + 15
            box_x = (WINDOW_WIDTH - box_width) // 2
            box_y = WINDOW_HEIGHT // 2 + 150

            bg_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(self.screen, ORANGE, bg_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, bg_rect, width=2, border_radius=8)

            text_rect.center = (WINDOW_WIDTH // 2, box_y + box_height // 2)
            self.screen.blit(text_surface, text_rect)
            self.action_effect_timer -= 1

    # -------------------- Core game loop helpers --------------------
    def step_ai(self):
        """
        Execute a single AI move:
          - Ask game for valid cards for current player
          - Ask corresponding agent to choose an action
          - Play card or draw if needed
          - Handle wild color selection via the game API
          - Enforce GUI-level UNO rule: track when a player reaches 1 card,
            auto-call UNO for AI with a probability, and apply +2 penalty if missed.
        """
        cp = self.game.current_player
        player_name = f"P{cp+1} ({self.agent_names[cp]})"

        # Acquire state & valid actions from game engine
        state = self.game.get_state_for_ai(cp)
        valid = self.game.get_valid_cards(cp)

        if valid:
            # Agents choose index (index refers to position in player's hand)
            action_index = self.agents[cp].choose_action(state, valid)
            card = self.game.hands[cp][action_index]

            if card.color == Color.WILD:
                # Let the game/engine pick a color for wild (uses engine logic)
                chosen_color = self.game.choose_color_for_wild(cp)
                self.game.play_card(cp, action_index, chosen_color)
                self.show_notification(f"{player_name} played WILD → {chosen_color.name}", LIGHT_GRAY, 60)
            else:
                # Normal play
                self.game.play_card(cp, action_index)
                self.show_notification(f"{player_name} played {card}", LIGHT_GRAY, 60)

                # Action card visual effects
                if card.card_type == CardType.DRAW_TWO:
                    self.show_action_effect(f"💥 {player_name} played +2!")
                elif card.card_type == CardType.WILD_DRAW_FOUR:
                    self.show_action_effect(f"💥💥 {player_name} played +4!")
                elif card.card_type == CardType.SKIP:
                    self.show_action_effect(f"⏭️ {player_name} played Skip!")
                elif card.card_type == CardType.REVERSE:
                    self.show_action_effect(f"🔄 {player_name} played Reverse!")
        else:
            # No valid play -> draw. If pending_draw exists, draw multiple.
            pending = getattr(self.game, "pending_draw", 0)
            if pending > 0:
                self.game.draw_multiple_cards(cp, pending)
                self.show_notification(f"{player_name} drew {pending} cards!", RED, 90)
                self.game.pending_draw = 0
            else:
                # Regular single card draw provided by game object
                self.game.draw_card(cp)
                self.show_notification(f"{player_name} drew a card", LIGHT_GRAY, 60)

        # ---- UNO GUI-level enforcement ----
        # If player now has exactly 1 card, record the time and let AI possibly auto-call UNO.
        new_count = len(self.game.hands[cp])
        now_ms = pygame.time.get_ticks()

        if new_count == 1 and self.uno_time[cp] is None:
            # They just reached 1 card: start tracking
            self.uno_time[cp] = now_ms
            self.uno_called[cp] = False

            # AI auto-call behavior: high chance to call UNO correctly
            if random.random() < self.ai_uno_call_prob:
                self.uno_called[cp] = True
                self.show_notification(f"{player_name} says UNO!", CYAN, 60)
            else:
                # AI "forgets" to call UNO — will be catchable by others for a window
                self.show_notification(f"{player_name} forgot to say UNO!", RED, 90)

        # Check for UNO catch windows: if player didn't call UNO and the window elapsed,
        # apply penalty (draw 2). For simplicity, we auto-catch and penalize.
        for p in range(self.num_players):
            if self.uno_time[p] is not None and not self.uno_called[p]:
                elapsed = now_ms - self.uno_time[p]
                if elapsed >= self.uno_catch_window_ms:
                    # The next player is the one that "catches" them in this simplified rule.
                    caught_by = (p + 1) % self.num_players
                    # Apply penalty via game engine method (draw_multiple_cards)
                    self.game.draw_multiple_cards(p, 2)
                    self.show_notification(f"P{caught_by+1} caught P{p+1} — P{p+1} draws 2!", RED, self.uno_penalty_message_duration)
                    # Reset UNO tracking for that player
                    self.uno_time[p] = None
                    self.uno_called[p] = False

        # If someone has won (game.game_over should be set by engine), do NOT switch turn.
        if not self.game.game_over:
            # Let the game engine decide next player (switch_turn should honor Skip/Reverse logic)
            self.game.switch_turn()

    def toggle_speed(self):
        """Cycle through available speeds and recompute move_delay."""
        current_idx = self.speeds.index(self.game_speed) if self.game_speed in self.speeds else 0
        self.game_speed = self.speeds[(current_idx + 1) % len(self.speeds)]
        # Lower bound to avoid zero or negative delays
        self.move_delay = max(10, int(self.base_delay_unit_ms / self.game_speed))
        self.show_notification(f"Speed: {self.game_speed}x", CYAN, 60)

    def handle_back_to_start(self):
        """
        Return to the main start menu (cleanly).
        We do this by quitting pygame and importing StartMenu from start_menu.py,
        then calling StartMenu().run(). This keeps everything in a single process and
        avoids running multiple Pygame windows/processes.
        """
        # First quit current pygame subsystems to avoid conflicts
        pygame.quit()

        # Import and run the StartMenu loop — this will create a fresh pygame window.
        # It is safe because we've called pygame.quit() above.
        try:
            from start_menu import StartMenu
        except Exception as e:
            # If import fails, print helpful error and exit to avoid hanging.
            print("Failed to import StartMenu from start_menu.py:", e)
            sys.exit(1)

        # Run the StartMenu loop (blocking). When it returns, program flow continues.
        StartMenu().run()
        # If StartMenu().run() ever returns, exit to be safe
        sys.exit(0)

    # -------------------- Main loop --------------------
    def run(self):
        """Main Pygame loop for AI vs AI mode."""
        running = True
        while running:
            self.clock.tick(FPS)

            # ---- Event handling ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    # BACK -> return to start menu (import & run StartMenu)
                    if self.back_button_rect.collidepoint((mx, my)):
                        # Cleanly switch to start menu
                        self.handle_back_to_start()
                        # handle_back_to_start will not return normally
                        continue

                    # NEW GAME -> reset engine & UNO GUI trackers
                    if self.new_game_button_rect.collidepoint((mx, my)):
                        self.game.reset()
                        self.uno_called = {i: False for i in range(self.num_players)}
                        self.uno_time = {i: None for i in range(self.num_players)}
                        self.show_notification("New game started!", GREEN, 60)
                        continue

                    # END GAME -> quit program
                    if self.end_game_button_rect.collidepoint((mx, my)):
                        running = False
                        continue

                    # SPEED toggle
                    if self.speed_button_rect.collidepoint((mx, my)):
                        self.toggle_speed()
                        continue

            # ---- AI move timing ----
            now = pygame.time.get_ticks()
            if now - self.last_move_time >= self.move_delay and not self.game.game_over:
                self.step_ai()
                self.last_move_time = now

            # ---- Drawing ----
            self.screen.fill(GREEN)

            # Draw discard/deck area & info box
            self.draw_discard_pile()

            # Top bar buttons (consistent alignment)
            self.draw_button(self.back_button_rect, "BACK", PURPLE)
            self.draw_button(self.end_game_button_rect, "END GAME", RED)
            self.draw_button(self.new_game_button_rect, "NEW GAME", DARK_GREEN)
            self.draw_button(self.speed_button_rect, f"SPEED\n{self.game_speed}x", CYAN)

            # Draw stats box
            self.draw_stats()

            # Draw hands layout according to number of players
            if self.num_players == 2:
                # Top player
                self.draw_player_hand(0, 120, face_up=True)
                # Bottom player
                self.draw_player_hand(1, WINDOW_HEIGHT - 180, face_up=True)

                # Labels with clearer alignment
                p1_label = self.small_font.render(f"P1 ({self.agent_names[0]}): {len(self.game.hands[0])} cards", True, WHITE)
                p2_label = self.small_font.render(f"P2 ({self.agent_names[1]}): {len(self.game.hands[1])} cards", True, WHITE)
                self.screen.blit(p1_label, (20, 90))
                self.screen.blit(p2_label, (20, WINDOW_HEIGHT - 210))

            elif self.num_players == 3:
                self.draw_player_hand(0, 120, face_up=True)
                self.draw_player_hand(1, WINDOW_HEIGHT // 2 - 60, face_up=True)
                self.draw_player_hand(2, WINDOW_HEIGHT - 180, face_up=True)

            elif self.num_players == 4:
                # For 4 players we display two rows of hands
                self.draw_player_hand(0, 120, face_up=True)
                self.draw_player_hand(1, 120, face_up=True)
                self.draw_player_hand(2, WINDOW_HEIGHT - 180, face_up=True)
                self.draw_player_hand(3, WINDOW_HEIGHT - 180, face_up=True)

            # Turn indicator (center top)
            current = getattr(self.game, "current_player", 0)
            turn_text = f"P{current+1}'s TURN ({self.agent_names[current]})"
            turn_surface = self.font.render(turn_text, True, YELLOW)
            # Slightly lower so it doesn't overlap top buttons
            turn_rect = turn_surface.get_rect(center=(WINDOW_WIDTH // 2, 95))
            self.screen.blit(turn_surface, turn_rect)

            # Notifications & action effects
            self.draw_notification()
            self.draw_action_effect()

            # Game over overlay (if engine sets game_over True and winner)
            if getattr(self.game, "game_over", False):
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (0, 0))

                winner_idx = getattr(self.game, "winner", 0)
                winner_text = f"🎉 P{winner_idx + 1} ({self.agent_names[winner_idx]}) WINS! 🎉"
                text = self.font.render(winner_text, True, (0, 255, 0))
                text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.screen.blit(text, text_rect)

                restart_text = self.small_font.render("Click NEW GAME to play again", True, WHITE)
                restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
                self.screen.blit(restart_text, restart_rect)

            pygame.display.flip()

        # Clean up Pygame and exit when loop ends
        pygame.quit()
        sys.exit()


# -------------------- If run directly --------------------
if __name__ == "__main__":
    print("=" * 70)
    print("UNO - AI vs AI (updated)")
    print("=" * 70)
    print("Controls:")
    print("- BACK: Return to start menu")
    print("- NEW GAME: Restart a game")
    print("- END GAME: Quit the program")
    print("- SPEED: Cycle speeds (includes 0.1x & 0.25x for slow motion)")
    print("\nStarting AI vs AI...")
    print("=" * 70)

    AIVsAIGUI(num_players=2, base_move_delay=0.5).run()
