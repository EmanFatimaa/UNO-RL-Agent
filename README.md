# 1. Install dependencies
pip install pygame numpy

# 2. Run the game
python gui.py
```

## 🎮 **What You'll See:**

- **Your cards** at the bottom (click to play)
- **AI cards** at top (face down)
- **Discard pile** in center
- **Stats** showing AI learning progress
- **Buttons**: DRAW, TRAIN AI, NEW GAME

## 🧠 **How Learning Works:**

1. **Click "TRAIN AI"** → Watch terminal as AI plays 500 games against itself
2. **Win rate increases** → AI is learning!
3. **Play against it** → Now it's smart!
4. **Auto-saves** → Next time you run, it loads the trained brain

## 💡 **Understanding the Code:**

**uno_game.py**: Everything heavily commented
- `Card` class: What a card is
- `UnoGame` class: Game rules and flow
- No complex stuff, just game logic

**ql_agent.py**: The magic happens here
- `q_table`: The AI's memory
- `choose_action()`: How it decides
- `update_q_value()`: Where learning happens (Q-learning formula)

**gui.py**: Connects everything
- Pygame draws the game
- Handles your clicks
- Calls AI when it's AI's turn

## 🎯 **File Organization:**
```
your_folder/
├── uno_game.py     ← Create this (game logic)
├── ql_agent.py     ← Create this (AI brain)
├── gui.py          ← Create this (RUN THIS!)
└── README.txt      ← Create this (instructions)