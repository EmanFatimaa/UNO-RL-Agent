# Q-Learning AI agent
"""
Q-Learning Agent for UNO
This AI learns which cards to play by trial and error
"""

import random
import pickle
from collections import defaultdict

class QLearningAgent:
    """
    Q-Learning AI that learns to play UNO
    
    How it works:
    - Q-table stores "quality" of each action in each state
    - Higher Q-value = better action
    - Learns by playing games and updating Q-values based on results
    """
    
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.2):
        """
        Initialize the agent
        alpha: learning rate (how much to update Q-values)
        gamma: discount factor (how much to value future rewards)
        epsilon: exploration rate (chance to try random moves)
        """
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.games_played = 0
        self.games_won = 0
    
    def state_to_key(self, state):
        """
        Convert game state to a string key for the Q-table
        We simplify the state to make learning faster:
        - Number of cards by color in hand
        - Top card info
        - Current color
        """
        hand = state['hand']
        top_card = state['top_card']
        
        # Count cards by color
        color_counts = {c: 0 for c in range(5)}  # 5 colors including wild
        for card in hand:
            color_counts[card.color.value] += 1
        
        # Simplified state representation
        state_key = (
            tuple(color_counts.values()),  # Cards by color
            top_card.color.value,
            top_card.card_type.value,
            top_card.number if top_card.number else -1,
            state['current_color'].value,
            len(hand),  # Hand size
            state['player_card_count']  # Opponent's card count
        )
        return state_key
    
    def get_q_value(self, state, action):
        """Get Q-value for a state-action pair"""
        state_key = self.state_to_key(state)
        return self.q_table[state_key][action]
    
    def choose_action(self, state, valid_actions):
        """
        Choose an action using epsilon-greedy strategy
        - With probability epsilon: explore (random valid action)
        - Otherwise: exploit (best known action)
        """
        if not valid_actions:
            return None  # No valid actions (need to draw)
        
        # Exploration: try random action
        if random.random() < self.epsilon:
            return random.choice(valid_actions)
        
        # Exploitation: choose action with highest Q-value
        state_key = self.state_to_key(state)
        q_values = {action: self.q_table[state_key][action] for action in valid_actions}
        
        # If multiple actions have same Q-value, pick randomly among them
        max_q = max(q_values.values())
        best_actions = [a for a, q in q_values.items() if q == max_q]
        return random.choice(best_actions)
    
    def update_q_value(self, state, action, reward, next_state, next_valid_actions, done):
        """
        Update Q-value using Q-learning formula:
        Q(s,a) = Q(s,a) + alpha * (reward + gamma * max(Q(s',a')) - Q(s,a))
        
        This is where learning happens!
        """
        state_key = self.state_to_key(state)
        current_q = self.q_table[state_key][action]
        
        if done:
            # No future rewards if game is over
            max_next_q = 0
        else:
            # Find best action in next state
            next_state_key = self.state_to_key(next_state)
            if next_valid_actions:
                max_next_q = max([self.q_table[next_state_key][a] for a in next_valid_actions])
            else:
                max_next_q = 0
        
        # Q-learning update rule
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q
    
    def get_action_confidences(self, state, valid_actions):
        """
        Get Q-values for all valid actions (for visualization)
        Returns dictionary: {action: confidence}
        """
        if not valid_actions:
            return {}
        
        state_key = self.state_to_key(state)
        confidences = {}
        for action in valid_actions:
            confidences[action] = self.q_table[state_key][action]
        
        return confidences
    
    def get_win_rate(self):
        """Calculate current win rate"""
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played
    
    def save_model(self, filename="uno_agent.pkl"):
        """Save Q-table to file"""
        with open(filename, 'wb') as f:
            pickle.dump({
                'q_table': dict(self.q_table),
                'games_played': self.games_played,
                'games_won': self.games_won
            }, f)
        print(f"Model saved to {filename}")
    
    def load_model(self, filename="uno_agent.pkl"):
        """Load Q-table from file"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.q_table = defaultdict(lambda: defaultdict(float), data['q_table'])
                self.games_played = data['games_played']
                self.games_won = data['games_won']
            print(f"Model loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"No saved model found at {filename}")
            return False


def train_agent(num_episodes=1000, show_progress=True):
    """
    Train the agent by having it play against itself
    This is called from the GUI in training mode
    """
    from uno_game import UnoGame
    
    agent = QLearningAgent(alpha=0.15, gamma=0.9, epsilon=0.3)
    
    for episode in range(num_episodes):
        game = UnoGame()
        states = [None, None]
        actions = [None, None]
        
        while not game.game_over:
            current_player = game.current_player
            state = game.get_state_for_ai()
            valid_actions = game.get_valid_cards(game.ai_hand if current_player == 1 else game.player_hand)
            
            # Choose action
            if valid_actions:
                action = agent.choose_action(state, valid_actions)
                success = game.play_card(current_player, action)
                if success:
                    reward = 0.1  # Small reward for playing a card
                    if game.game_over and game.winner == current_player:
                        reward = 10  # Big reward for winning
                        agent.games_won += 1
            else:
                # Draw card if no valid moves
                game.draw_card(current_player)
                action = None
                reward = -0.1  # Small penalty for drawing
            
            # Store for learning
            states[current_player] = state
            actions[current_player] = action
            
            if not game.game_over:
                game.switch_turn()
            
            # Update Q-values for previous player if applicable
            if action is not None and states[current_player] is not None:
                next_state = game.get_state_for_ai()
                next_valid = game.get_valid_cards(game.ai_hand if current_player == 1 else game.player_hand)
                agent.update_q_value(states[current_player], action, reward, 
                                   next_state, next_valid, game.game_over)
        
        agent.games_played += 1
        
        # Print progress
        if show_progress and (episode + 1) % 100 == 0:
            win_rate = agent.get_win_rate()
            print(f"Episode {episode + 1}/{num_episodes} | Win Rate: {win_rate:.2%} | Q-table size: {len(agent.q_table)}")
    
    return agent