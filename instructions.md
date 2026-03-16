# pacman_duel Instructions

## Required Packages

- Python 3.12+
- `PySide6`
- `pytest` for running tests

Example install:

```bash
pip install PySide6 pytest
```

## Run Command

From the repository root:

```bash
python src/app.py
```

Alternative module form:

```bash
python -m src.app
```

## Menu Overview

The top control panel stays visible during gameplay.

- `Board`: choose the built-in maze layout
- `Pacman`: choose human control or Pacman random AI
- `Slime AI`: choose the slime-side algorithm
- `Helper AI`: choose the helper algorithm
- `Enemy speed scaling`: choose fixed slower movement or `Adaptive`

Buttons:

- `Start Match`: start a match using the current settings
- `Replay Current Config`: restart immediately with the same settings
- `Stop Match`: stop the current match but keep the controls visible
- `Quit App`: close the application

In-game controls:

- Arrow keys: move Pacman
- `r`: replay with the current config
- `q` or `Esc`: stop the current match
