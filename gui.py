"""
UNO Game GUI using Pygame - INTERACTIVE VERSION
Run this file to play!

Controls:
- Click on a card in your hand to play it
- Click "DRAW" button to draw a card
- Click "TRAIN AI" to watch the AI learn
- Click "NEW GAME" to restart
"""

import pygame
import sys
from uno_game import UnoGame, Color, CardType
from ql_agent import QLearningAgent, train_agent

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Card dimensions
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_RADIUS = 10

class UnoGUI:
    """Main GUI class that handles all rendering and user interaction"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("UNO - Q-Learning AI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        # Game components
        self.game = UnoGame()
        self.agent = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=0.15)
        
        # Try to load pre-trained model
        self.agent.load_model()
        
        # UI state
        self.selected_card = None
        self.hovered_card = None
        self.choosing_color = False
        self.training_mode = False
        self.ai_delay = 0
        
        # Animation state
        self.animating_card = None  # Card being animated
        self.animation_start_pos = None
        self.animation_end_pos = None
        self.animation_progress = 0
        self.animation_speed = 0.1
        
        # Notification system
        self.notification = ""
        self.notification_timer = 0
        self.notification_color = WHITE
        
        # Button rectangles
        self.draw_button_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT // 2 - 40, 120, 80)
        self.train_button_rect = pygame.Rect(20, 20, 150, 40)
        self.new_game_button_rect = pygame.Rect(190, 20, 150, 40)
        self.stats_rect = pygame.Rect(WINDOW_WIDTH - 250, 20, 230, 120)
        
        # Deck click area
        self.deck_rect = pygame.Rect(WINDOW_WIDTH // 2 - CARD_WIDTH - 120, 
                                     WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2, 
                                     CARD_WIDTH, CARD_HEIGHT)
    
    def show_notification(self, message, color=WHITE, duration=120):
        """Show a notification message"""
        self.notification = message
        self.notification_color = color
        self.notification_timer = duration
    
    def start_animation(self, card, start_pos, end_pos):
        """Start card animation"""
        self.animating_card = card
        self.animation_start_pos = start_pos
        self.animation_end_pos = end_pos
        self.animation_progress = 0
    
    def update_animation(self):
        """Update card animation"""
        if self.animating_card:
            self.animation_progress += self.animation_speed
            if self.animation_progress >= 1.0:
                self.animating_card = None
                self.animation_progress = 0
    
    def draw_card(self, card, x, y, face_up=True, highlight=False, glow=False):
        """Draw a single card at given position"""
        # Glow effect for valid cards
        if glow:
            glow_rect = pygame.Rect(x - 5, y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10)
            pygame.draw.rect(self.screen, YELLOW, glow_rect, border_radius=CARD_RADIUS + 2)
        
        # Card background
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
            # Card color strip
            card_color = card.get_color_rgb()
            pygame.draw.rect(self.screen, card_color, 
                           (x + 10, y + 10, CARD_WIDTH - 20, CARD_HEIGHT - 20),
                           border_radius=5)
            
            # Card text
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
    
    def draw_player_hand(self, hand, y_pos, face_up=True, check_valid=False):
        """Draw a player's hand of cards"""
        spacing = 90
        total_width = len(hand) * spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        card_rects = []
        valid_cards = self.game.get_valid_cards(hand) if check_valid else []
        
        for i, card in enumerate(hand):
            x = start_x + i * spacing
            highlight = (self.selected_card == i and face_up)
            glow = False  # Disabled card glow - let player figure it out
            
            self.draw_card(card, x, y_pos, face_up, highlight, glow)
            card_rects.append(pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT))
        
        return card_rects, valid_cards
    
    def draw_discard_pile(self):
        """Draw the discard pile in the center"""
        top_card = self.game.get_top_card()
        x = WINDOW_WIDTH // 2 - CARD_WIDTH - 20
        y = WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2
        
        # Draw deck - UNO card back style
        deck_color = (50, 50, 50)  # Dark gray
        
        # Main deck card
        pygame.draw.rect(self.screen, deck_color, 
                        (x - 100, y, CARD_WIDTH, CARD_HEIGHT), 
                        border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, BLACK, 
                        (x - 100, y, CARD_WIDTH, CARD_HEIGHT), 
                        width=3, border_radius=CARD_RADIUS)
        
        # Draw UNO back pattern - red circle with "UNO"
        center_x = x - 100 + CARD_WIDTH // 2
        center_y = y + CARD_HEIGHT // 2
        
        # Red circle
        pygame.draw.circle(self.screen, (220, 20, 60), (center_x, center_y), 28)
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 28, 2)
        
        # UNO text
        uno_text = self.small_font.render("UNO", True, WHITE)
        uno_rect = uno_text.get_rect(center=(center_x, center_y))
        self.screen.blit(uno_text, uno_rect)
        
        # Deck count below
        deck_count = self.tiny_font.render(f"{len(self.game.deck)} cards", True, WHITE)
        self.screen.blit(deck_count, (x - 95, y + CARD_HEIGHT + 5))
        
        # Draw top card
        self.draw_card(top_card, x + 20, y, face_up=True)
        
        # Show current color with bigger emphasis
        color_bg = pygame.Rect(x - 10, y + CARD_HEIGHT + 30, 180, 30)
        pygame.draw.rect(self.screen, WHITE, color_bg, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, color_bg, width=2, border_radius=5)
        
        color_text = self.small_font.render(f"Color: {self.game.current_color.name}", 
                                           True, BLACK)
        self.screen.blit(color_text, (x, y + CARD_HEIGHT + 35))
    
    def draw_button(self, rect, text, color=DARK_GREEN, enabled=True):
        """Draw a button"""
        btn_color = color if enabled else GRAY
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=5)
        text_surface = self.small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def draw_stats(self):
        """Draw AI statistics"""
        pygame.draw.rect(self.screen, WHITE, self.stats_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.stats_rect, width=2, border_radius=5)
        
        stats_lines = [
            f"AI Games: {self.agent.games_played}",
            f"AI Wins: {self.agent.games_won}",
            f"Win Rate: {self.agent.get_win_rate():.1%}",
            f"Q-States: {len(self.agent.q_table)}"
        ]
        
        for i, line in enumerate(stats_lines):
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (self.stats_rect.x + 10, self.stats_rect.y + 10 + i * 25))
    
    def draw_notification(self):
        """Draw notification message"""
        if self.notification_timer > 0:
            # Create notification box
            text_surface = self.font.render(self.notification, True, BLACK)
            text_rect = text_surface.get_rect()
            
            box_width = text_rect.width + 40
            box_height = text_rect.height + 20
            box_x = (WINDOW_WIDTH - box_width) // 2
            box_y = WINDOW_HEIGHT // 2 - 200
            
            # Draw semi-transparent background
            bg_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(self.screen, self.notification_color, bg_rect, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, bg_rect, width=3, border_radius=10)
            
            # Draw text
            text_rect.center = (WINDOW_WIDTH // 2, box_y + box_height // 2)
            self.screen.blit(text_surface, text_rect)
            
            self.notification_timer -= 1
    
    def draw_color_choice(self):
        """Draw color selection UI for wild cards"""
        colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
        color_names = ["RED", "BLUE", "GREEN", "YELLOW"]
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Instruction text
        instruction = self.font.render("Choose a color!", True, WHITE)
        inst_rect = instruction.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 120))
        self.screen.blit(instruction, inst_rect)
        
        # Color choice boxes
        box_size = 100
        start_x = (WINDOW_WIDTH - len(colors) * (box_size + 20)) // 2
        y = WINDOW_HEIGHT // 2 - box_size // 2
        
        rects = []
        for i, (color, name) in enumerate(zip(colors, color_names)):
            x = start_x + i * (box_size + 20)
            rect = pygame.Rect(x, y, box_size, box_size)
            
            color_rgb = self.get_color_rgb(color)
            
            # Hover effect
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
        """Helper to get RGB for a color enum"""
        color_map = {
            Color.RED: (220, 20, 60),
            Color.BLUE: (30, 144, 255),
            Color.GREEN: (50, 205, 50),
            Color.YELLOW: (255, 215, 0)
        }
        return color_map[color]
    
    def handle_player_turn(self, mouse_pos, card_rects, valid_cards):
        """Handle player's card selection"""
        # Check if clicked on a card
        for i, rect in enumerate(card_rects):
            if rect.collidepoint(mouse_pos):
                card = self.game.player_hand[i]
                
                # Check if card is valid
                if card.can_play_on(self.game.get_top_card(), self.game.current_color):
                    if card.color == Color.WILD:
                        self.selected_card = i
                        self.choosing_color = True
                        self.show_notification("Choose a color!", LIGHT_GRAY, 60)
                    else:
                        # Play the card
                        if self.game.play_card(0, i):
                            self.show_notification(f"You played {card}!", GREEN, 60)
                            if not self.game.game_over:
                                self.game.switch_turn()
                                self.ai_delay = 30
                else:
                    # Invalid card
                    self.show_notification("Invalid card! Must match color or number", RED, 90)
                return
        
        # Check if clicked deck
        if self.deck_rect.collidepoint(mouse_pos):
            drawn = self.game.draw_card(0)
            if drawn:
                self.show_notification(f"Drew: {drawn}", LIGHT_GRAY, 60)
                self.game.switch_turn()
                self.ai_delay = 30
    
    def handle_ai_turn(self):
        """Handle AI's turn"""
        if self.ai_delay > 0:
            self.ai_delay -= 1
            return
        
        state = self.game.get_state_for_ai()
        valid_actions = self.game.get_valid_cards(self.game.ai_hand)
        
        if valid_actions:
            action = self.agent.choose_action(state, valid_actions)
            card = self.game.ai_hand[action]
            
            if card.color == Color.WILD:
                chosen_color = self.game.choose_color_for_wild(self.game.ai_hand)
                self.game.play_card(1, action, chosen_color)
                self.show_notification(f"AI played {card.card_type.name}, chose {chosen_color.name}", LIGHT_GRAY)
            else:
                self.game.play_card(1, action)
                self.show_notification(f"AI played {card}", LIGHT_GRAY)
            
            if not self.game.game_over:
                self.game.switch_turn()
        else:
            self.game.draw_card(1)
            self.show_notification("AI drew a card", LIGHT_GRAY)
            self.game.switch_turn()
    
    def run_training(self, num_episodes=500):
        """Run training mode - AI plays against itself"""
        self.training_mode = True
        self.show_notification("Training AI... Check terminal!", YELLOW, 180)
        print(f"\nTraining AI for {num_episodes} games...")
        
        trained_agent = train_agent(num_episodes, show_progress=True)
        self.agent = trained_agent
        self.agent.save_model()
        
        print(f"\nTraining complete!")
        print(f"Win rate: {self.agent.get_win_rate():.2%}")
        print(f"Q-table size: {len(self.agent.q_table)} states")
        
        self.training_mode = False
        self.game.reset()
        self.show_notification("Training complete! AI is ready!", GREEN, 120)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            self.clock.tick(FPS)
            
            # Get mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()
            
            # Update hover state for player cards
            if self.game.current_player == 0 and not self.game.game_over:
                spacing = 90
                total_width = len(self.game.player_hand) * spacing
                start_x = (WINDOW_WIDTH - total_width) // 2
                y_pos = WINDOW_HEIGHT - 150
                
                self.hovered_card = None
                for i in range(len(self.game.player_hand)):
                    x = start_x + i * spacing
                    rect = pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT)
                    if rect.collidepoint(mouse_pos):
                        self.hovered_card = i
                        break
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and not self.training_mode:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Color selection
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
                                    self.ai_delay = 30
                        continue
                    
                    # Train button
                    if self.train_button_rect.collidepoint(mouse_pos):
                        self.run_training(500)
                        continue
                    
                    # New game button
                    if self.new_game_button_rect.collidepoint(mouse_pos):
                        self.game.reset()
                        self.selected_card = None
                        self.show_notification("New game started!", GREEN)
                        continue
                    
                    # Player's turn - need to rebuild card_rects properly
                    if self.game.current_player == 0 and not self.game.game_over:
                        spacing = 90
                        total_width = len(self.game.player_hand) * spacing
                        start_x = (WINDOW_WIDTH - total_width) // 2
                        y_pos = WINDOW_HEIGHT - 150
                        
                        # Build proper card rectangles
                        card_rects = []
                        for i in range(len(self.game.player_hand)):
                            x = start_x + i * spacing
                            card_rects.append(pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT))
                        
                        valid_cards = self.game.get_valid_cards(self.game.player_hand)
                        self.handle_player_turn(mouse_pos, card_rects, valid_cards)
            
            # AI's turn
            if self.game.current_player == 1 and not self.game.game_over and not self.training_mode:
                self.handle_ai_turn()
            
            # Update animations
            self.update_animation()
            
            # Drawing
            self.screen.fill(GREEN)
            
            # Draw game elements
            self.draw_discard_pile()
            self.draw_button(self.train_button_rect, "TRAIN AI")
            self.draw_button(self.new_game_button_rect, "NEW GAME")
            self.draw_stats()
            
            # Draw hands with validity checking for player
            card_rects, valid_cards = self.draw_player_hand(self.game.player_hand, WINDOW_HEIGHT - 150, 
                                                            face_up=True, check_valid=True)
            self.draw_player_hand(self.game.ai_hand, 80, face_up=False, check_valid=False)  # Moved down from 50 to 80
            
            # Draw turn indicator
            turn_text = "YOUR TURN!" if self.game.current_player == 0 else "AI's Turn..."
            turn_color = YELLOW if self.game.current_player == 0 else LIGHT_GRAY
            turn_surface = self.font.render(turn_text, True, turn_color)
            turn_rect = turn_surface.get_rect(center=(WINDOW_WIDTH // 2, 30))
            self.screen.blit(turn_surface, turn_rect)
            
            # Draw card count indicators
            player_count = self.small_font.render(f"Your cards: {len(self.game.player_hand)}", True, WHITE)
            ai_count = self.small_font.render(f"AI cards: {len(self.game.ai_hand)}", True, WHITE)
            self.screen.blit(player_count, (20, WINDOW_HEIGHT - 50))
            self.screen.blit(ai_count, (20, 110))  # Moved down from 80 to 110
            
            # Draw notification
            self.draw_notification()
            
            # Color choice overlay
            if self.choosing_color:
                self.draw_color_choice()
            
            # Game over message
            if self.game.game_over:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (0, 0))
                
                winner_text = "🎉 YOU WIN! 🎉" if self.game.winner == 0 else "AI WINS!"
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
    print("=" * 60)
    print("UNO with Q-Learning AI - INTERACTIVE VERSION")
    print("=" * 60)
    print("\nControls:")
    print("- Click glowing cards in your hand to play")
    print("- Click deck (left card) to draw if no valid moves")
    print("- Click TRAIN AI to teach the AI (500 games)")
    print("- Click NEW GAME to restart")
    print("\nStarting game...")
    print("=" * 60)
    
    game = UnoGUI()
    game.run()