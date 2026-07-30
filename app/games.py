import json
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
GAMES_PATH = BASE_DIR / "config" / "games.json"

def load_games() -> List[Dict[str, Any]]:
    with GAMES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def get_game_profile(game_id: str) -> Optional[Dict[str, Any]]:
    for g in load_games():
        if g["id"] == game_id:
            return g
    return None