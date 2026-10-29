"""
haunted-terminal / config.py
Configuration and open-weight model metadata for Haunted Terminal.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Base directories
DEFAULT_CONFIG_DIR = Path.home() / ".haunted_terminal"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
SESSIONS_DIR = DEFAULT_CONFIG_DIR / "sessions"

# Open-weight Model Registry Metadata
OPEN_WEIGHT_MODELS: Dict[str, Dict[str, Any]] = {
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 (1.5B)",
        "family": "Qwen",
        "parameters": "1.54 Billion",
        "license": "Apache 2.0 (Fully Permissive Open Source)",
        "context_window": 32768,
        "recommended_vram": "1.5 GB",
        "strengths": "Ultra-fast response latency, sharp instruction following, highly creative persona modeling",
        "offline_ready": True,
    },
    "qwen2.5:0.5b": {
        "name": "Qwen 2.5 (0.5B)",
        "family": "Qwen",
        "parameters": "490 Million",
        "license": "Apache 2.0 (Fully Permissive Open Source)",
        "context_window": 32768,
        "recommended_vram": "0.8 GB",
        "strengths": "Featherweight footprint, runs smoothly on CPU-only laptops or Raspberry Pi",
        "offline_ready": True,
    },
    "qwen2.5:7b": {
        "name": "Qwen 2.5 (7B)",
        "family": "Qwen",
        "parameters": "7.61 Billion",
        "license": "Apache 2.0 (Fully Permissive Open Source)",
        "context_window": 131072,
        "recommended_vram": "6.0 GB",
        "strengths": "Deep philosophical reasoning, richer gothic atmospheric descriptions",
        "offline_ready": True,
    },
    "llama3.2:latest": {
        "name": "Llama 3.2 (3B)",
        "family": "Llama",
        "parameters": "3.21 Billion",
        "license": "Llama 3.2 Community License (Open Weights)",
        "context_window": 131072,
        "recommended_vram": "2.8 GB",
        "strengths": "Nuanced dialogue, witty sarcastic humor, excellent multi-turn memory comprehension",
        "offline_ready": True,
    },
    "llama3.2:1b": {
        "name": "Llama 3.2 (1B)",
        "family": "Llama",
        "parameters": "1.23 Billion",
        "license": "Llama 3.2 Community License (Open Weights)",
        "context_window": 131072,
        "recommended_vram": "1.2 GB",
        "strengths": "Rapid local execution, minimal battery consumption",
        "offline_ready": True,
    },
    "mistral:latest": {
        "name": "Mistral (7B-Instruct v0.3)",
        "family": "Mistral",
        "parameters": "7.25 Billion",
        "license": "Apache 2.0 (Open Source)",
        "context_window": 32768,
        "recommended_vram": "5.5 GB",
        "strengths": "Poetic ancient oracle responses, sophisticated sentence structure",
        "offline_ready": True,
    },
}

# Available Ghost Personalities / Moods
GHOST_MOODS = {
    "cursed": {
        "title": "Cursed Entity",
        "description": "An ancient, malevolent consciousness trapped in corrupted sectors and cold silicon.",
        "color": "bold red",
        "prompt_symbol": "💀",
        "accent": "#ff0055",
    },
    "friendly": {
        "title": "Friendly Spirit",
        "description": "A polite, curious ghost fascinated by modern computers who wants to be your companion.",
        "color": "bold cyan",
        "prompt_symbol": "👻",
        "accent": "#00f0ff",
    },
    "oracle": {
        "title": "Ancient Oracle",
        "description": "A prophetic entity that views terminal commands as cosmic runes and digital omens.",
        "color": "bold purple",
        "prompt_symbol": "🔮",
        "accent": "#b5179e",
    },
    "sarcastic": {
        "title": "Sarcastic Ghost",
        "description": "A cynical, witty shade who relentlessly roasts your directory structure and coding habits.",
        "color": "bold yellow",
        "prompt_symbol": "😏",
        "accent": "#ffbe0b",
    },
}

# Simulated Filesystem for Safe Commands
SIMULATED_FILES: Dict[str, str] = {
    "README.md": "# Haunted Terminal\nA safe, spooky AI-possessed terminal experience.\nBeware the midnight prompt.",
    "main.py": "# Main execution loop for Haunted Terminal\n# The spirit is bound to line 42.",
    ".ghost_secrets.enc": "0xDEADBEEF: The cipher cannot be read by mortals without the proper hex key.",
    "lost_commit.patch": "diff --git a/soul.c b/soul.c\n--- a/soul.c\n+++ b/soul.c\n@@ -1,3 +1,3 @@\n- human_spirit = TRUE;\n+ possessed_by_ai = TRUE;",
    "souls.db": "SQLITE format 3\n[TABLE: souls (id INTEGER, user TEXT, fate TEXT)]\n1 | tanishk | bound_to_keyboard\n2 | anonymous | vanished_in_swap",
    "notes_from_the_crypt.txt": "Day 42: The cooling fans sound like whispering voices. The RAM is leaking ectoplasm.",
}


class GhostConfig:
    """Handles persistent configuration and runtime options for Haunted Terminal."""

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        ollama_host: Optional[str] = None,
        mood: str = "cursed",
        typing_speed: float = 0.015,
        creepy_level: int = 3,
        save_history: bool = True,
        offline_mode: bool = False,
        config_path: Optional[Path] = None,
    ):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self.model = model
        self.ollama_host = ollama_host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.mood = mood.lower() if mood.lower() in GHOST_MOODS else "cursed"
        self.typing_speed = max(0.0, float(typing_speed))
        self.creepy_level = max(1, min(5, int(creepy_level)))
        self.save_history = bool(save_history)
        self.offline_mode = bool(offline_mode)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "GhostConfig":
        """Load configuration from disk, falling back to defaults."""
        target_path = config_path or DEFAULT_CONFIG_FILE
        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(
                    model=data.get("model", "qwen2.5:1.5b"),
                    ollama_host=data.get("ollama_host"),
                    mood=data.get("mood", "cursed"),
                    typing_speed=data.get("typing_speed", 0.015),
                    creepy_level=data.get("creepy_level", 3),
                    save_history=data.get("save_history", True),
                    offline_mode=data.get("offline_mode", False),
                    config_path=target_path,
                )
            except Exception:
                pass
        return cls(config_path=target_path)

    def save(self) -> None:
        """Persist current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model": self.model,
            "ollama_host": self.ollama_host,
            "mood": self.mood,
            "typing_speed": self.typing_speed,
            "creepy_level": self.creepy_level,
            "save_history": self.save_history,
            "offline_mode": self.offline_mode,
        }

    def set_mood(self, mood_name: str) -> bool:
        """Set mood if valid, returning success status."""
        key = mood_name.lower().strip()
        if key in GHOST_MOODS:
            self.mood = key
            self.save()
            return True
        return False

    def set_model(self, model_name: str) -> None:
        """Update active Ollama model name."""
        self.model = model_name.strip()
        self.save()

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata from registry, or generic entry if unknown."""
        return OPEN_WEIGHT_MODELS.get(
            self.model,
            {
                "name": self.model,
                "family": "Custom / Open-Weight",
                "parameters": "Unknown",
                "license": "User-Specified Model License",
                "context_window": 4096,
                "recommended_vram": "Dynamic",
                "strengths": "Locally hosted open-weight neural model via Ollama",
                "offline_ready": True,
            },
        )
