# # Q-Learning AI agent
# """
# Q-Learning Agent for UNO
# This AI learns which cards to play by trial and error
# """

# import random
# import pickle
# from collections import defaultdict

# class QLearningAgent:
#     """
#     Q-Learning AI that learns to play UNO
    
#     How it works:
#     - Q-table stores "quality" of each action in each state
#     - Higher Q-value = better action
#     - Learns by playing games and updating Q-values based on results
#     """
    
#     def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.2):
#         """
#         Initialize the agent
#         alpha: learning rate (how much to update Q-values)
#         gamma: discount factor (how much to value future rewards)
#         epsilon: exploration rate (chance to try random moves)
#         """
#         self.q_table = defaultdict(lambda: defaultdict(float))
#         self.alpha = alpha
#         self.gamma = gamma
#         self.epsilon = epsilon
#         self.games_played = 0
#         self.games_won = 0
    
#     def state_to_key(self, state):
#         """
#         Convert game state to a string key for the Q-table
#         We simplify the state to make learning faster:
#         - Number of cards by color in hand
#         - Top card info
#         - Current color
#         """
#         hand = state['hand']
#         top_card = state['top_card']
        
#         # Count cards by color
#         color_counts = {c: 0 for c in range(5)}  # 5 colors including wild
#         for card in hand:
#             color_counts[card.color.value] += 1
        
#         # Simplified state representation
#         state_key = (
#             tuple(color_counts.values()),  # Cards by color
#             top_card.color.value,
#             top_card.card_type.value,
#             top_card.number if top_card.number else -1,
#             state['current_color'].value,
#             len(hand),  # Hand size
#             state['player_card_count']  # Opponent's card count
#         )
#         return state_key
    
#     def get_q_value(self, state, action):
#         """Get Q-value for a state-action pair"""
#         state_key = self.state_to_key(state)
#         return self.q_table[state_key][action]
    
#     def choose_action(self, state, valid_actions):
#         """
#         Choose an action using epsilon-greedy strategy
#         - With probability epsilon: explore (random valid action)
#         - Otherwise: exploit (best known action)
#         """
#         if not valid_actions:
#             return None  # No valid actions (need to draw)
        
#         # Exploration: try random action
#         if random.random() < self.epsilon:
#             return random.choice(valid_actions)
        
#         # Exploitation: choose action with highest Q-value
#         state_key = self.state_to_key(state)
#         q_values = {action: self.q_table[state_key][action] for action in valid_actions}
        
#         # If multiple actions have same Q-value, pick randomly among them
#         max_q = max(q_values.values())
#         best_actions = [a for a, q in q_values.items() if q == max_q]
#         return random.choice(best_actions)
    
#     def update_q_value(self, state, action, reward, next_state, next_valid_actions, done):
#         """
#         Update Q-value using Q-learning formula:
#         Q(s,a) = Q(s,a) + alpha * (reward + gamma * max(Q(s',a')) - Q(s,a))
        
#         This is where learning happens!
#         """
#         state_key = self.state_to_key(state)
#         current_q = self.q_table[state_key][action]
        
#         if done:
#             # No future rewards if game is over
#             max_next_q = 0
#         else:
#             # Find best action in next state
#             next_state_key = self.state_to_key(next_state)
#             if next_valid_actions:
#                 max_next_q = max([self.q_table[next_state_key][a] for a in next_valid_actions])
#             else:
#                 max_next_q = 0
        
#         # Q-learning update rule
#         new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
#         self.q_table[state_key][action] = new_q
    
#     def get_action_confidences(self, state, valid_actions):
#         """
#         Get Q-values for all valid actions (for visualization)
#         Returns dictionary: {action: confidence}
#         """
#         if not valid_actions:
#             return {}
        
#         state_key = self.state_to_key(state)
#         confidences = {}
#         for action in valid_actions:
#             confidences[action] = self.q_table[state_key][action]
        
#         return confidences
    
#     def get_win_rate(self):
#         """Calculate current win rate"""
#         if self.games_played == 0:
#             return 0.0
#         return self.games_won / self.games_played
    
#     def save_model(self, filename="uno_agent.pkl"):
#         """Save Q-table to file"""
#         with open(filename, 'wb') as f:
#             pickle.dump({
#                 'q_table': dict(self.q_table),
#                 'games_played': self.games_played,
#                 'games_won': self.games_won
#             }, f)
#         print(f"Model saved to {filename}")
    
#     def load_model(self, filename="uno_agent.pkl"):
#         """Load Q-table from file"""
#         try:
#             with open(filename, 'rb') as f:
#                 data = pickle.load(f)
#                 self.q_table = defaultdict(lambda: defaultdict(float), data['q_table'])
#                 self.games_played = data['games_played']
#                 self.games_won = data['games_won']
#             print(f"Model loaded from {filename}")
#             return True
#         except FileNotFoundError:
#             print(f"No saved model found at {filename}")
#             return False


# def train_agent(num_episodes=1000, show_progress=True):
#     """
#     Train the agent by having it play against itself
#     This is called from the GUI in training mode
#     """
#     from uno_game import UnoGame
    
#     agent = QLearningAgent(alpha=0.15, gamma=0.9, epsilon=0.3)
    
#     for episode in range(num_episodes):
#         game = UnoGame()
#         states = [None, None]
#         actions = [None, None]
        
#         while not game.game_over:
#             current_player = game.current_player
#             state = game.get_state_for_ai()
#             valid_actions = game.get_valid_cards(game.ai_hand if current_player == 1 else game.player_hand)
            
#             # Choose action
#             if valid_actions:
#                 action = agent.choose_action(state, valid_actions)
#                 success = game.play_card(current_player, action)
#                 if success:
#                     reward = 0.1  # Small reward for playing a card
#                     if game.game_over and game.winner == current_player:
#                         reward = 10  # Big reward for winning
#                         agent.games_won += 1
#             else:
#                 # Draw card if no valid moves
#                 game.draw_card(current_player)
#                 action = None
#                 reward = -0.1  # Small penalty for drawing
            
#             # Store for learning
#             states[current_player] = state
#             actions[current_player] = action
            
#             if not game.game_over:
#                 game.switch_turn()
            
#             # Update Q-values for previous player if applicable
#             if action is not None and states[current_player] is not None:
#                 next_state = game.get_state_for_ai()
#                 next_valid = game.get_valid_cards(game.ai_hand if current_player == 1 else game.player_hand)
#                 agent.update_q_value(states[current_player], action, reward, 
#                                    next_state, next_valid, game.game_over)
        
#         agent.games_played += 1
        
#         # Print progress
#         if show_progress and (episode + 1) % 100 == 0:
#             win_rate = agent.get_win_rate()
#             print(f"Episode {episode + 1}/{num_episodes} | Win Rate: {win_rate:.2%} | Q-table size: {len(agent.q_table)}")
    
#     return agent

# ql_agent.py
"""
Corrected Q-Learning agent module for UNO
- Backwards-compatible with GUI expectations
- Provides RandomAgent and HeuristicAgent
- Training helpers accept an agent instance (GUI passes its agent)
"""

import random
import pickle
from collections import defaultdict, deque
from typing import Optional

# ---------------------------------------------------------
# Q-Learning Agent
# ---------------------------------------------------------
class QLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.2, name="QLearning", epsilon_min=0.05, epsilon_decay=0.9995):
        """
        alpha: learning rate
        gamma: discount factor
        epsilon: initial exploration rate
        name: friendly label (used in GUI)
        epsilon_min, epsilon_decay: simple adaptive epsilon schedule
        """
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.name = name

        # stats
        self.games_played = 0
        self.games_won = 0
        self.rewards_history = deque(maxlen=500)  # recent episode total rewards

    # -----------------------
    # State handling
    # -----------------------
    def state_to_key(self, state):
        """
        Create a compact, hashable state key from the state dictionary.
        This function is defensive: it accepts multiple possible key names
        produced by different versions of UnoGame.
        Expected fields used (if present):
          - 'hand' : list of Card
          - 'top_card' : Card
          - 'current_color' : Color enum
          - 'player_card_count' or 'opponent_card_count' or 'my_card_count'
          - 'my_card_count' (or we will deduce from hand)
        """
        hand = state.get('hand', [])
        top_card = state.get('top_card')

        # safe color counts (color.value assumed 0..4)
        color_counts = [0] * 5
        for card in hand:
            try:
                color_counts[card.color.value] += 1
            except Exception:
                # fallback if not enum-like
                pass

        # robust lookups for opponent/player counts
        opponent_count = state.get('player_card_count',
                          state.get('opponent_card_count',
                          state.get('opponent_card_count', None)))
        if opponent_count is None:
            opponent_count = state.get('my_card_count', len(hand))  # fallback

        # top card info (defensive)
        if top_card is None:
            top_color = -1
            top_type = -1
            top_number = -1
        else:
            top_color = getattr(top_card.color, 'value', -1)
            top_type = getattr(top_card.card_type, 'value', -1)
            top_number = getattr(top_card, 'number', -1) if getattr(top_card, 'number', None) is not None else -1

        state_key = (
            tuple(color_counts),
            top_color,
            top_type,
            top_number,
            getattr(state.get('current_color'), 'value', -1),
            len(hand),
            int(opponent_count)
        )
        return state_key

    # -----------------------
    # Q interface
    # -----------------------
    def get_q_value(self, state, action):
        state_key = self.state_to_key(state)
        return self.q_table[state_key][action]

    def choose_action(self, state, valid_actions):
        """Epsilon-greedy. valid_actions is a list of indices into hand"""
        if not valid_actions:
            return None

        # explore
        if random.random() < self.epsilon:
            return random.choice(valid_actions)

        state_key = self.state_to_key(state)
        # ensure all valid actions exist in table
        q_values = {a: self.q_table[state_key][a] for a in valid_actions}
        max_q = max(q_values.values())
        best = [a for a, q in q_values.items() if q == max_q]
        return random.choice(best)

    def update_q_value(self, state, action, reward, next_state, next_valid_actions, done):
        state_key = self.state_to_key(state)
        current_q = self.q_table[state_key][action]

        if done or next_state is None:
            max_next_q = 0
        else:
            next_key = self.state_to_key(next_state)
            if next_valid_actions:
                max_next_q = max([self.q_table[next_key][a] for a in next_valid_actions])
            else:
                max_next_q = 0

        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q

    def get_action_confidences(self, state, valid_actions):
        if not valid_actions:
            return {}
        state_key = self.state_to_key(state)
        return {a: self.q_table[state_key][a] for a in valid_actions}

    # -----------------------
    # Stats helpers (used by GUI)
    # -----------------------
    def record_episode_reward(self, total_reward):
        self.rewards_history.append(total_reward)

    def get_win_rate(self):
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played

    def get_average_reward(self):
        if not self.rewards_history:
            return 0.0
        return sum(self.rewards_history) / len(self.rewards_history)

    def get_adaptive_epsilon(self):
        return self.epsilon

    def decay_epsilon(self):
        # simple decay for long training runs
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            if self.epsilon < self.epsilon_min:
                self.epsilon = self.epsilon_min

    # -----------------------
    # Persistence
    # -----------------------
    def save_model(self, filename="uno_agent.pkl"):
        # Convert nested defaultdict to normal dicts for pickling
        serial = {}
        for s, inner in self.q_table.items():
            serial[s] = dict(inner)
        payload = {
            'q_table': serial,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'rewards_history': list(self.rewards_history),
            'epsilon': self.epsilon
        }
        with open(filename, 'wb') as f:
            pickle.dump(payload, f)
        print(f"[QLearningAgent] Model saved to {filename}")

    def load_model(self, filename="uno_agent.pkl"):
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            # rebuild nested defaultdict
            new_q = defaultdict(lambda: defaultdict(float))
            for s, inner in data.get('q_table', {}).items():
                # inner is a dict mapping actions to floats
                new_q[s] = defaultdict(float, inner)
            self.q_table = new_q
            self.games_played = data.get('games_played', 0)
            self.games_won = data.get('games_won', 0)
            self.rewards_history = deque(data.get('rewards_history', []), maxlen=500)
            self.epsilon = data.get('epsilon', self.epsilon)
            print(f"[QLearningAgent] Model loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"[QLearningAgent] No saved model found at {filename}")
            return False

# ---------------------------------------------------------
# Simple opponent agents (as GUI expects)
# ---------------------------------------------------------
class RandomAgent:
    def __init__(self, name="Random"):
        self.name = name
        self.games_played = 0
        self.games_won = 0

    def choose_action(self, state, valid_actions):
        if not valid_actions:
            return None
        return random.choice(valid_actions)

    def get_action_confidences(self, state, valid_actions):
        # uniform small confidence so GUI can display something
        if not valid_actions:
            return {}
        val = 1.0 / len(valid_actions)
        return {a: val for a in valid_actions}

    def get_average_reward(self):
        return 0.0

    def get_adaptive_epsilon(self):
        return 0.0

class HeuristicAgent:
    """
    Very small heuristic: prefers action cards, wilds, then highest number.
    Not smart but deterministic enough for GUI opponent.
    """
    def __init__(self, name="Heuristic"):
        self.name = name
        self.games_played = 0
        self.games_won = 0

    def choose_action(self, state, valid_actions):
        if not valid_actions:
            return None
        hand = state.get('hand', [])
        # prefer draw+skip+wild in that order
        best_score = None
        best_action = None
        for a in valid_actions:
            card = hand[a]
            score = 0
            if card.card_type.name in ("WILD_DRAW_FOUR", "WILD"):
                score += 50
            if card.card_type.name == "DRAW_TWO":
                score += 30
            if card.card_type.name == "SKIP":
                score += 20
            if card.card_type == getattr(card, 'card_type'):
                pass
            # number preference
            if card.card_type.name == "NUMBER" and getattr(card, 'number', None) is not None:
                score += card.number
            if best_score is None or score > best_score:
                best_score = score
                best_action = a
        return best_action

    def get_action_confidences(self, state, valid_actions):
        if not valid_actions:
            return {}
        # return small heuristic confidences (bigger for higher heuristic score)
        confidences = {}
        hand = state.get('hand', [])
        scores = []
        for a in valid_actions:
            card = hand[a]
            score = 0
            if card.card_type.name in ("WILD_DRAW_FOUR", "WILD"):
                score += 50
            if card.card_type.name == "DRAW_TWO":
                score += 30
            if card.card_type.name == "SKIP":
                score += 20
            if card.card_type == getattr(card, 'card_type'):
                pass
            if card.card_type.name == "NUMBER" and getattr(card, 'number', None) is not None:
                score += card.number
            scores.append((a, score))
        max_score = max(s for _, s in scores) or 1.0
        for a, s in scores:
            confidences[a] = s / max_score
        return confidences

# ---------------------------------------------------------
# Training helpers
# ---------------------------------------------------------
def train_agent(agent: Optional[QLearningAgent] = None,
                num_episodes: int = 1000,
                opponent_type: str = 'mixed',
                show_progress: bool = True):
    """
    Train `agent`. If agent is None, creates a new QLearningAgent.
    opponent_type:
      - 'mixed' uses alternating opponents for variety (heuristic/random)
      - 'self' agent plays against itself
      - 'random' plays against RandomAgent
    Returns the trained agent.
    """
    from uno_game import UnoGame

    if agent is None:
        agent = QLearningAgent(alpha=0.15, gamma=0.9, epsilon=0.3, name="Q-Agent")

    # opponent switching simple policy
    opponents = {
        'random': RandomAgent(),
        'heuristic': HeuristicAgent()
    }

    for episode in range(num_episodes):
        game = UnoGame()
        total_rewards = [0.0, 0.0]  # reward per player this episode
        # we will treat agent as player 1 (AI) for consistency with earlier design
        # if opponent_type == 'self' the agent will control both players (simpler)
        while not game.game_over:
            current_player = game.current_player
            # create state from current player's perspective consistent with earlier code
            state = game.get_state_for_ai(perspective_player=current_player) if 'perspective_player' in game.get_state_for_ai.__code__.co_varnames else game.get_state_for_ai()
            hand = game.ai_hand if current_player == 1 else game.player_hand
            valid_actions = game.get_valid_cards(hand)

            # pick acting agent
            if opponent_type == 'self':
                acting_agent = agent
            elif opponent_type == 'random':
                acting_agent = opponents['random']
            elif opponent_type == 'heuristic':
                acting_agent = opponents['heuristic']
            elif opponent_type == 'mixed':
                # mix behavior: if current_player is 1 -> our agent, else alternate random/heuristic
                if current_player == 1:
                    acting_agent = agent
                else:
                    acting_agent = opponents['random'] if (episode % 2 == 0) else opponents['heuristic']
            else:
                acting_agent = opponents.get(opponent_type, opponents['random'])

            if valid_actions:
                action = acting_agent.choose_action(state, valid_actions)
                success = game.play_card(current_player, action)
                if success:
                    reward = 0.1  # small reward for playing a card
                    # big reward for winning
                    if game.game_over and game.winner == current_player:
                        reward = 10.0
                else:
                    reward = -0.5
            else:
                # draw a card
                game.draw_card(current_player)
                action = None
                reward = -0.05

            # bookkeeping for learning updates only if agent was the one who acted
            if current_player == 1:
                total_rewards[1] += reward
                # update Q for agent's previous chosen action if applicable
                # (we need to store previous state/action — to keep simple, do immediate update)
                # obtain next state and next_valid for update
                next_state = game.get_state_for_ai(perspective_player=1) if 'perspective_player' in game.get_state_for_ai.__code__.co_varnames else game.get_state_for_ai()
                next_valid = game.get_valid_cards(game.ai_hand)
                if action is not None:
                    agent.update_q_value(state, action, reward, next_state, next_valid, game.game_over)
            else:
                total_rewards[0] += reward

            # step turn
            if not game.game_over:
                game.switch_turn()

        # episode finished
        agent.games_played += 1
        if game.winner == 1:
            agent.games_won += 1

        # record episode reward for statistics & decay epsilon a bit
        agent.record_episode_reward(sum(total_rewards))
        agent.decay_epsilon()

        if show_progress and (episode + 1) % 100 == 0:
            print(f"Episode {episode+1}/{num_episodes} | Win Rate: {agent.get_win_rate():.2%} | Q-States: {len(agent.q_table)} | Epsilon: {agent.get_adaptive_epsilon():.4f}")

    return agent

def train_with_curriculum(agent: Optional[QLearningAgent] = None, show_progress=True):
    """
    Example curriculum: train first vs random, then vs heuristic, then vs mixed self-play.
    This is a convenience function the GUI imports.
    """
    if agent is None:
        agent = QLearningAgent(alpha=0.15, gamma=0.9, epsilon=0.3, name="Q-Agent")

    print("[Curriculum] Stage 1: vs random (1000)")
    train_agent(agent, num_episodes=1000, opponent_type='random', show_progress=show_progress)
    print("[Curriculum] Stage 2: vs heuristic (1000)")
    train_agent(agent, num_episodes=1000, opponent_type='heuristic', show_progress=show_progress)
    print("[Curriculum] Stage 3: mixed/self (2000)")
    train_agent(agent, num_episodes=2000, opponent_type='mixed', show_progress=show_progress)

# convenience wrapper to preserve old signature (if any code calls old train_agent(num_episodes))
def train_agent_legacy(num_episodes=1000, show_progress=True):
    return train_agent(None, num_episodes=num_episodes, opponent_type='mixed', show_progress=show_progress)
