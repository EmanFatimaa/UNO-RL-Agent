# This file is the full Human-vs-AI UNO GUI that displays the game state, handles user clicks, chooses AI moves, shows action-card effects, and provides training/testing tools for Q-learning agent.

import pygame
import sys
from uno_game import UnoGame, Color, CardType
from ql_agent import QLearningAgent, RandomAgent, HeuristicAgent, train_agent, train_with_curriculum

pygame.init()

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60

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

CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_RADIUS = 10

class UnoGUI:
    """CORRECTED GUI with action card effects"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("SMART UNO - RL AGENT")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        self.game = UnoGame()
        self.agent = QLearningAgent(alpha=0.15, gamma=0.95, epsilon=0.25, name="Q-Agent")
        self.agent.load_model()
        
        self.selected_card = None
        self.hovered_card = None
        self.choosing_color = False
        self.training_mode = False
        self.show_q_values = False
        self.ai_delay = 0
        
        self.opponent_type = 'q-learning'
        self.opponents = {
            'q-learning': self.agent,
            'random': RandomAgent(),
            'heuristic': HeuristicAgent()
        }
        
        self.notification = ""
        self.notification_timer = 0
        self.notification_color = WHITE
        
        # Action effect display
        self.action_effect = ""
        self.action_effect_timer = 0
        
        
        # Buttons
        self.train_button_rect = pygame.Rect(20, 20, 150, 40)
        self.train_curriculum_rect = pygame.Rect(180, 20, 150, 40)

        self.new_game_button_rect = pygame.Rect(WINDOW_WIDTH//2 - 75, 65, 150, 40)
        self.end_game_button_rect = pygame.Rect(WINDOW_WIDTH//2 - 500, 65, 150, 40)
        self.toggle_q_button_rect = pygame.Rect(WINDOW_WIDTH - 500, 20, 150, 40)
        self.opponent_button_rect = pygame.Rect(WINDOW_WIDTH - 340, 20, 150, 40)

        # Stats (moved down)
        self.stats_rect = pygame.Rect(WINDOW_WIDTH - 260, 300, 240, 200)

        # Deck rect (necessary!)
        self.deck_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - CARD_WIDTH - 120,
            WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2,
            CARD_WIDTH, CARD_HEIGHT
        )



    
    def show_notification(self, message, color=WHITE, duration=120):
        self.notification = message
        self.notification_color = color
        self.notification_timer = duration
    
    def show_action_effect(self, message, duration=180):
        """Show action card effects"""
        self.action_effect = message
        self.action_effect_timer = duration
    def end_game(self):
        """Immediately stop the game and close the window."""
        if self.simulation_running:
            # Stop the simulation loop safely
            self.simulation_running = False

        # Destroy the Tkinter window and exit the program
        self.root.destroy()

    def draw_card(self, card, x, y, face_up=True, highlight=False, glow=False, q_value=None):
        if glow:
            glow_rect = pygame.Rect(x - 5, y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10)
            pygame.draw.rect(self.screen, YELLOW, glow_rect, border_radius=CARD_RADIUS + 2)
        
        color = WHITE if face_up else GRAY
        if highlight:
            pygame.draw.rect(self.screen, ORANGE, 
                           (x - 3, y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6), 
                           border_radius=CARD_RADIUS)
        
        pygame.draw.rect(self.screen, color, (x, y, CARD_WIDTH, CARD_HEIGHT), 
                        border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 
                        width=2, border_radius=CARD_RADIUS)
        
        if face_up:
            card_color = card.get_color_rgb()
            pygame.draw.rect(self.screen, card_color, 
                           (x + 10, y + 10, CARD_WIDTH - 20, CARD_HEIGHT - 20),
                           border_radius=5)
            
            if card.card_type == CardType.NUMBER:
                text = str(card.number)
            else:
                type_names = {
                    CardType.SKIP: "Skip",
                    CardType.REVERSE: "Rev",
                    CardType.DRAW_TWO: "+2",
                    CardType.WILD: "Wild",
                    CardType.WILD_DRAW_FOUR: "+4"
                }
                text = type_names.get(card.card_type, "?")
            
            text_surface = self.font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
            self.screen.blit(text_surface, text_rect)
            
            if q_value is not None and self.show_q_values:
                q_text = self.tiny_font.render(f"Q:{q_value:.2f}", True, BLACK)
                q_bg = pygame.Rect(x + 2, y + 2, 70, 18)
                pygame.draw.rect(self.screen, YELLOW, q_bg, border_radius=3)
                self.screen.blit(q_text, (x + 4, y + 4))
    
    def draw_player_hand(self, hand, y_pos, face_up=True, check_valid=False, show_q=False, state=None):
        spacing = 90
        total_width = len(hand) * spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        card_rects = []
        valid_cards = self.game.get_valid_cards(hand) if check_valid else []
        
        q_values = {}
        if show_q and state and face_up:
            q_values = self.agent.get_action_confidences(state, valid_cards)
        
        for i, card in enumerate(hand):
            x = start_x + i * spacing
            highlight = (self.selected_card == i and face_up)
            glow = (i in valid_cards and face_up)
            q_val = q_values.get(i, None) if show_q else None
            
            self.draw_card(card, x, y_pos, face_up, highlight, glow, q_val)
            card_rects.append(pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT))
        
        return card_rects, valid_cards
    
    def draw_discard_pile(self):
        top_card = self.game.get_top_card()
        x = WINDOW_WIDTH // 2 - CARD_WIDTH - 20
        y = WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2
        
        deck_color = (50, 50, 50)
        pygame.draw.rect(self.screen, deck_color, 
                        (x - 100, y, CARD_WIDTH, CARD_HEIGHT), 
                        border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, 
                        (x - 100, y, CARD_WIDTH, CARD_HEIGHT), 
                        width=3, border_radius=CARD_RADIUS)
        
        center_x = x - 100 + CARD_WIDTH // 2
        center_y = y + CARD_HEIGHT // 2
        pygame.draw.circle(self.screen, (220, 20, 60), (center_x, center_y), 28)
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 28, 2)
        uno_text = self.small_font.render("UNO", True, WHITE)
        uno_rect = uno_text.get_rect(center=(center_x, center_y))
        self.screen.blit(uno_text, uno_rect)
        
        deck_count = self.tiny_font.render(f"{len(self.game.deck)} cards", True, WHITE)
        self.screen.blit(deck_count, (x - 95, y + CARD_HEIGHT + 5))
        
        self.draw_card(top_card, x + 20, y, face_up=True)
        
        # Show current color and pending effects
        info_y = y + CARD_HEIGHT + 30
        color_bg = pygame.Rect(x - 10, info_y, 180, 30)
        pygame.draw.rect(self.screen, WHITE, color_bg, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, color_bg, width=2, border_radius=5)
        color_text = self.small_font.render(f"Color: {self.game.current_color.name}", True, BLACK)
        self.screen.blit(color_text, (x, info_y + 5))
        
        # Show pending draw
        if self.game.pending_draw > 0:
            pending_bg = pygame.Rect(x - 10, info_y + 40, 180, 30)
            pygame.draw.rect(self.screen, RED, pending_bg, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, pending_bg, width=2, border_radius=5)
            pending_text = self.small_font.render(f"+{self.game.pending_draw} PENDING!", True, WHITE)
            self.screen.blit(pending_text, (x, info_y + 45))
    
    def draw_button(self, rect, text, color=DARK_GREEN, enabled=True):
        btn_color = color if enabled else GRAY
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=5)
        
        lines = text.split('\n')
        if len(lines) == 1:
            text_surface = self.small_font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
        else:
            for i, line in enumerate(lines):
                text_surface = self.tiny_font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery - 10 + i * 20))
                self.screen.blit(text_surface, text_rect)
    
    def draw_stats(self):
        pygame.draw.rect(self.screen, WHITE, self.stats_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.stats_rect, width=2, border_radius=5)
        
        stats_lines = [
            f"AI: {self.agent.name}",
            f"Games: {self.agent.games_played}",
            f"Wins: {self.agent.games_won}",
            f"Win Rate: {self.agent.get_win_rate():.1%}",
            f"Avg Reward: {self.agent.get_average_reward():.1f}",
            f"Q-States: {len(self.agent.q_table)}",
            f"Epsilon: {self.agent.get_adaptive_epsilon():.3f}",
            f"Opponent: {self.opponent_type.title()}",
            f"",
            f"Game Info:",
            f"Turns: {self.game.turns_played}"
        ]
        
        # for i, line in enumerate(stats_lines):
        #     text = self.tiny_font.render(line, True, BLACK)
        #     self.screen.blit(text, (self.stats_rect.x + 10, self.stats_rect.y + 10 + i * 19))
        for i, line in enumerate(stats_lines):
            text = self.tiny_font.render(line, True, BLACK)
            self.screen.blit(text, (self.stats_rect.x + 10, self.stats_rect.y + 10 + i * 16))

    
    def draw_notification(self):
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
        """Draw action card effect notification"""
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
    
    def draw_color_choice(self):
        colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
        color_names = ["RED", "BLUE", "GREEN", "YELLOW"]
        
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        instruction = self.font.render("Choose a color!", True, WHITE)
        inst_rect = instruction.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 120))
        self.screen.blit(instruction, inst_rect)
        
        box_size = 100
        start_x = (WINDOW_WIDTH - len(colors) * (box_size + 20)) // 2
        y = WINDOW_HEIGHT // 2 - box_size // 2
        
        rects = []
        for i, (color, name) in enumerate(zip(colors, color_names)):
            x = start_x + i * (box_size + 20)
            rect = pygame.Rect(x, y, box_size, box_size)
            
            color_rgb = self.get_color_rgb(color)
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                hover_rect = pygame.Rect(x - 5, y - 5, box_size + 10, box_size + 10)
                pygame.draw.rect(self.screen, YELLOW, hover_rect, border_radius=15)
            
            pygame.draw.rect(self.screen, color_rgb, rect, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, rect, width=3, border_radius=10)
            
            text = self.small_font.render(name, True, WHITE)
            text_rect = text.get_rect(center=(x + box_size // 2, y + box_size + 20))
            self.screen.blit(text, text_rect)
            
            rects.append((rect, color))
        
        return rects
    
    def get_color_rgb(self, color):
        color_map = {
            Color.RED: (220, 20, 60),
            Color.BLUE: (30, 144, 255),
            Color.GREEN: (50, 205, 50),
            Color.YELLOW: (255, 215, 0)
        }
        return color_map[color]
    def handle_player_turn(self, mouse_pos, card_rects, valid_cards):
        # --- PLAY CARD ---
        for i, rect in enumerate(card_rects):
            if rect.collidepoint(mouse_pos):
                card = self.game.player_hand[i]

                # Check if card is valid to play
                if i not in valid_cards:
                    self.show_notification("Invalid card! Must match color/number/type.", RED, 90)
                    return

                # Wild requires color selection
                if card.color == Color.WILD:
                    self.selected_card = i
                    self.choosing_color = True
                    self.show_notification("Choose a color!", LIGHT_GRAY, 60)
                    return

                # Play normal or action card
                played = self.game.play_card(0, i)
                if played:
                    # Apply messages
                    if card.card_type == CardType.DRAW_TWO:
                        self.show_action_effect("💥 You played +2! AI must draw 2!")
                    elif card.card_type==CardType.WILD_DRAW_FOUR:  
                        self.show_action_effect("💥💥 you played +4! AI draws 4!")  
                    elif card.card_type == CardType.SKIP:
                        self.show_action_effect("⏭️ You played Skip!")
                    elif card.card_type == CardType.REVERSE:
                        self.show_action_effect("🔄 You played Reverse!")

                    self.show_notification(f"You played {card}!", GREEN, 60)

                    # If game not over → switch turn
                    # --- TURN LOGIC FIX FOR SKIP / REVERSE ---
                    if not self.game.game_over:
                        if card.card_type in (CardType.SKIP, CardType.REVERSE):
                            # player gets another turn → do NOT switch
                            self.show_notification("player gets another turn!", LIGHT_GRAY)
                            self.ai_delay = 40
                        else:
                            # Normal turn → switch to ai
                            self.game.switch_turn()

                return

        # --- DRAW CARD ---
        if self.deck_rect.collidepoint(mouse_pos):

            # If you owe cards (+2/+4)
            if self.game.pending_draw > 0:
                count = self.game.pending_draw
                self.game.draw_multiple_cards(0, count)
                self.show_notification(f"You drew {count} cards!", RED, 90)
                self.game.pending_draw = 0

                self.game.switch_turn()
                self.ai_delay = 40
                return

            # Normal draw
            drawn = self.game.draw_card(0)
            if drawn:
                self.show_notification(f"You drew: {drawn}", LIGHT_GRAY, 60)

                # If playable, allow playing it
                if drawn.can_play_on(self.game.get_top_card(), self.game.current_color):
                    self.selected_card = len(self.game.player_hand) - 1
                    self.show_notification("Playable! Click it to play.", GREEN, 60)
                    return

            # If drawn card was not playable → turn ends
            self.game.switch_turn()
            self.ai_delay = 40
    def handle_ai_turn(self):
        if self.ai_delay > 0:
            self.ai_delay -= 1
            return

        current_opponent = self.opponents[self.opponent_type]
        state = self.game.get_state_for_ai(perspective_player=1)
        valid_actions = self.game.get_valid_cards(self.game.ai_hand)

        # --- AI PLAYS CARD ---
        if valid_actions:
            action = current_opponent.choose_action(state, valid_actions)
            card = self.game.ai_hand[action]

            # Wild requires choosing color
            if card.color == Color.WILD:
                chosen_color = self.game.choose_color_for_wild(self.game.ai_hand)
                self.game.play_card(1, action, chosen_color)
                self.show_notification(f"AI played WILD → {chosen_color.name}", LIGHT_GRAY)

            else:
                self.game.play_card(1, action)

            # Action card messages
            if card.card_type == CardType.DRAW_TWO:
                self.show_action_effect("💥 AI played +2! You must draw 2!")
            elif card.card_type == CardType.WILD_DRAW_FOUR:
                self.show_action_effect("💥💥 AI played +4! You draw 4!")
            elif card.card_type == CardType.SKIP:
                self.show_action_effect("⏭️ AI played Skip! Your turn skipped!")
            elif card.card_type == CardType.REVERSE:
                self.show_action_effect("🔄 AI played Reverse!")

            self.show_notification(f"AI played {card}", LIGHT_GRAY)

            # --- TURN LOGIC FIX FOR SKIP / REVERSE ---
            if not self.game.game_over:
                if card.card_type in (CardType.SKIP, CardType.REVERSE):
                    # AI gets another turn → do NOT switch
                    self.show_notification("AI gets another turn!", LIGHT_GRAY)
                    self.ai_delay = 40
                else:
                    # Normal turn → switch to human
                    self.game.switch_turn()


        # --- AI HAS NO VALID CARD ---
        else:
            # Must draw because of pending draw
            if self.game.pending_draw > 0:
                count = self.game.pending_draw
                self.game.draw_multiple_cards(1, count)
                self.show_notification(f"AI drew {count} cards!", LIGHT_GRAY)
                self.game.pending_draw = 0

            else:
                # Normal draw
                drawn = self.game.draw_card(1)
                self.show_notification("AI drew a card", LIGHT_GRAY)

                # AI plays drawn card if playable
                if drawn and drawn.can_play_on(self.game.get_top_card(), self.game.current_color):
                    idx = len(self.game.ai_hand) - 1
                    card = self.game.ai_hand[idx]

                    if card.color == Color.WILD:
                        chosen_color = self.game.choose_color_for_wild(self.game.ai_hand)
                        self.game.play_card(1, idx, chosen_color)
                    else:
                        self.game.play_card(1, idx)

                    self.show_notification(f"AI played drawn {card}", LIGHT_GRAY)

            self.game.switch_turn()
    
    def run_training(self, num_episodes=1000, curriculum=False):
        self.training_mode = True
        
        if curriculum:
            self.show_notification("Curriculum Training... Check terminal!", YELLOW, 240)
            print("\n" + "="*60)
            print("STARTING CURRICULUM TRAINING")
            print("="*60)
            train_with_curriculum(self.agent, show_progress=True)
        else:
            self.show_notification(f"Training {num_episodes} games... Check terminal!", YELLOW, 180)
            print(f"\nTraining AI for {num_episodes} games...")
            train_agent(self.agent, num_episodes, opponent_type='mixed', show_progress=True)
        
        self.agent.save_model()
        print(f"\nTraining complete!")
        print(f"Win rate: {self.agent.get_win_rate():.2%}")
        print(f"Q-table size: {len(self.agent.q_table)} states")
        
        self.training_mode = False
        self.game.reset()
        self.show_notification("Training complete! AI is ready!", GREEN, 120)
    
    def cycle_opponent(self):
        types = ['q-learning', 'random', 'heuristic']
        current_idx = types.index(self.opponent_type)
        self.opponent_type = types[(current_idx + 1) % len(types)]
        self.show_notification(f"Opponent: {self.opponent_type.title()}", CYAN, 90)
    
    def run(self):
        running = True
        
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and not self.training_mode:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.choosing_color:
                        color_rects = self.draw_color_choice()
                        for rect, color in color_rects:
                            if rect.collidepoint(mouse_pos):
                                self.game.play_card(0, self.selected_card, color)
                                self.choosing_color = False
                                self.selected_card = None
                                self.show_notification(f"Chose {color.name}!", GREEN)
                                if not self.game.game_over:
                                    self.game.switch_turn()
                                    self.ai_delay = 40
                        continue
                    
                    if self.train_button_rect.collidepoint(mouse_pos):
                        self.run_training(1000, curriculum=False)
                        continue
                    
                    if self.train_curriculum_rect.collidepoint(mouse_pos):
                        self.run_training(curriculum=True)
                        continue
                    
                    if self.new_game_button_rect.collidepoint(mouse_pos):
                        self.game.reset()
                        self.selected_card = None
                        self.show_notification("New game started!", GREEN)
                        continue
                    if self.end_game_button_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

                    if self.toggle_q_button_rect.collidepoint(mouse_pos):
                        self.show_q_values = not self.show_q_values
                        status = "ON" if self.show_q_values else "OFF"
                        self.show_notification(f"Q-Values: {status}", CYAN, 60)
                        continue
                    
                    if self.opponent_button_rect.collidepoint(mouse_pos):
                        self.cycle_opponent()
                        continue
                    
                    if self.game.current_player == 0 and not self.game.game_over:
                        spacing = 90
                        total_width = len(self.game.player_hand) * spacing
                        start_x = (WINDOW_WIDTH - total_width) // 2
                        y_pos = WINDOW_HEIGHT - 180
                        
                        card_rects = []
                        for i in range(len(self.game.player_hand)):
                            x = start_x + i * spacing
                            card_rects.append(pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT))
                        
                        valid_cards = self.game.get_valid_cards(self.game.player_hand)
                        self.handle_player_turn(mouse_pos, card_rects, valid_cards)
            
            if self.game.current_player == 1 and not self.game.game_over and not self.training_mode:
                self.handle_ai_turn()
            
            self.screen.fill(GREEN)
            
            self.draw_discard_pile()
            self.draw_button(self.train_button_rect, "TRAIN AI\n(1000 games)", PURPLE)
            self.draw_button(self.train_curriculum_rect, "CURRICULUM\n(4000 games)", (100, 50, 150))
            self.draw_button(self.new_game_button_rect, "NEW GAME")
            self.draw_button(self.end_game_button_rect,"END GAME")
            # self.draw_button(self.toggle_q_button_rect, f"Q-VALUES\n({'ON' if self.show_q_values else 'OFF'})", ORANGE)
            self.draw_button(self.opponent_button_rect, f"OPPONENT:\n{self.opponent_type[:8].upper()}", CYAN)
            self.draw_stats()
            
            state = self.game.get_state_for_ai(0) if self.game.current_player == 0 else None
            card_rects, valid_cards = self.draw_player_hand(
                self.game.player_hand, WINDOW_HEIGHT - 180, 
                face_up=True, check_valid=True, show_q=self.show_q_values, state=state
            )
            self.draw_player_hand(self.game.ai_hand, 120, face_up=False)
            
            turn_text = "YOUR TURN!" if self.game.current_player == 0 else f"AI's Turn ({self.opponent_type})..."
            turn_color = YELLOW if self.game.current_player == 0 else LIGHT_GRAY
            turn_surface = self.font.render(turn_text, True, turn_color)
            turn_rect = turn_surface.get_rect(center=(WINDOW_WIDTH // 2, 35))
            self.screen.blit(turn_surface, turn_rect)
            
            player_count = self.small_font.render(f"Your cards: {len(self.game.player_hand)}", True, WHITE)
            ai_count = self.small_font.render(f"AI cards: {len(self.game.ai_hand)}", True, WHITE)
            self.screen.blit(player_count, (20, WINDOW_HEIGHT - 70))
            self.screen.blit(ai_count, (20, 110))
            
            self.draw_notification()
            self.draw_action_effect()
            
            if self.choosing_color:
                self.draw_color_choice()
            
            if self.game.game_over:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (0, 0))
                
                winner_text = "YOU WIN!" if self.game.winner == 0 else f"AI ({self.opponent_type.upper()}) WINS!"
                win_color = (0, 255, 0) if self.game.winner == 0 else (255, 50, 50)
                text = self.font.render(winner_text, True, win_color)
                text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.screen.blit(text, text_rect)
                
                restart_text = self.small_font.render("Click NEW GAME to play again", True, WHITE)
                restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
                self.screen.blit(restart_text, restart_rect)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    print("=" * 70)
    print("UNO with CORRECTED Q-Learning AI")
    print("=" * 70)
    print("\n🔧 CORRECTED FEATURES:")
    print("✓ Draw Two/Four now FORCE opponent to draw cards")
    print("✓ Skip properly skips opponent's turn")
    print("✓ Reverse changes turn direction")
    print("✓ Proper turn flow management")
    print("✓ Visual feedback for all action cards")
    print("✓ Enhanced reward system for action card strategy")
    print("\nControls:")
    print("- Click cards to play")
    print("- Click deck to draw (or draw pending cards)")
    print("- TRAIN AI: Quick training (1000 games)")
    print("- CURRICULUM: Advanced training 4000 games)")
    print("- Q-VALUES: Toggle Q-value display")
    print("- OPPONENT: Switch AI types")
    print("\nStarting game...")
    print("=" * 70)
    
    game = UnoGUI()
    game.run()