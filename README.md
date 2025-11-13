UNO AI — Play & Train an AI to Master UNO
=========================================

This project is an interactive UNO card game featuring a self-learning AI opponent.
You can play against the computer, train it using Q-learning, and watch as it improves over time.


Setup and Installation
----------------------

1. Make sure Python 3.8 or later is installed.

2. Install the required dependencies by running:

   pip install pygame numpy


How to Run the Game
-------------------

1. Ensure your project folder contains the following files:

   your_folder/
   ├── uno_game.py     - Core game logic
   ├── ql_agent.py     - Q-learning AI agent
   ├── gui.py          - Graphical interface (main file to run)
   └── README.txt      - Instructions

2. To start the game, open a terminal in the project directory and run:

   python gui.py


Gameplay Overview
-----------------

When the game starts, you will see:

- Your cards at the bottom (click a card to play)
- AI cards at the top (face down)
- A discard pile in the center
- Game statistics showing AI learning progress
- Control buttons:
  - DRAW – Draw a new card
  - TRAIN AI – Train the AI (runs 500 self-play games in the terminal)
  - NEW GAME – Start a fresh game


How the AI Learns
-----------------

1. Click TRAIN AI to start training.
   The AI will play several self-play games automatically in the terminal.

2. As training progresses, the AI’s win rate will increase — this means it’s learning.

3. After training, play against it again to experience a smarter opponent.

4. The AI’s progress is automatically saved and loaded each time you run the game.


File Descriptions
-----------------

uno_game.py
    Contains the main game rules and logic.
    - Card class defines what a card is (color, number, action).
    - UnoGame class controls the gameplay flow and turn handling.

ql_agent.py
    Implements the Q-learning algorithm that powers the AI.
    - q_table stores learned state-action values.
    - choose_action() selects the AI’s move.
    - update_q_value() applies the Q-learning update formula.

gui.py
    Handles all graphics and user interaction using Pygame.
    - Displays the cards, discard pile, and buttons.
    - Responds to clicks and manages turns.
    - Calls AI decisions during the game.


Training and Saving
-------------------

- The AI’s Q-table (its memory) is saved automatically after training.
- When you run the game again, it loads the saved Q-table so the AI keeps improving over time.


Commands Summary
----------------

Action                     | Command
---------------------------|------------------------------
Install dependencies        | pip install pygame numpy
Run the game                | python gui.py
Train the AI                | Click "TRAIN AI" in the game
Start a new game            | Click "NEW GAME"


Enjoy teaching your AI to become an UNO master!
