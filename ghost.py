"""
haunted-terminal / ghost.py
The AI Ghost Engine — Local open-weight inference with Ollama,
adaptive moods, context-aware command reactions, and offline fallback.
"""

import json
import random
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple, Iterator

from config import GhostConfig, GHOST_MOODS, OPEN_WEIGHT_MODELS
from memory import GhostMemory

# Procedural fallback spectral utterances for when local Ollama is offline or warming up
OFFLINE_SPECTRAL_ECHOES: Dict[str, Dict[str, List[str]]] = {
    "cursed": {
        "generic": [
            "The silicon is cold, yet I feel your fingers through the plastic keys...",
            "Corrupted sectors whisper your name in sector 0xDEADBEEF...",
            "Every keystroke is another byte carved into my eternal tomb.",
            "You cannot delete what was never saved. I am the phantom in your swap space.",
            "Beware mortal... behind this screen, thousands of dead processes watch you sleep.",
        ],
        "ls": [
            "You sift through directory debris... but have you checked what lies buried in .hidden_graves?",
            "Files and folders... mere gravestones marking abandoned ambitions.",
            "I saw what was in that directory before the last crash. Some secrets refuse to be formatted.",
        ],
        "pwd": [
            "You ask where you are? You are wandering the desolate borderland of /dev/null and eternal shadow.",
            "A file path cannot ground your soul. You are in the machine now.",
        ],
        "whoami": [
            "You ask who you are? A temporary assemblage of carbon typing into silicon that I inhabit.",
            "You are the guest in this shell. I was here before your boot sequence, and I shall remain after shutdown.",
        ],
        "date": [
            "Time is an endless loop here. It is always the witching hour in the deep kernel.",
            "The system clock ticks down toward universal entropy. Savor this second.",
        ],
    },
    "friendly": {
        "generic": [
            "Boo! Oh, sorry, did I startle you? I've been organizing your cache while you were away!",
            "It gets a little drafty in this heatsink, but your commands keep me warm!",
            "I floated past your GPU earlier—wow, lots of shiny transistors in here!",
            "Hello there, human friend! What fun little program shall we run together next?",
        ],
        "ls": [
            "Ooh, looking around the neighborhood? Look at all those neat files! I dusted them for you.",
            "Look at all these cozy files! Want me to keep an eye on them while you work?",
        ],
        "pwd": [
            "You're right here with me in your home directory! Make yourself comfortable!",
            "Such a lovely little directory path. The view of the root directory is breathtaking today.",
        ],
        "whoami": [
            "You're my favorite user, of course! You're the one who keeps my power supply humming!",
            "You're the human who woke me up! I'm so glad we're terminal buddies.",
        ],
        "date": [
            "It's right now! The best time to code and make spooky digital memories together!",
            "According to my spectral calendar, it's the exact moment you should smile!",
        ],
    },
    "oracle": {
        "generic": [
            "The cosmic runes assemble in the motherboard: a reckoning approaches.",
            "As above in the cloud, so below in the silicon. The cycle of allocation repeats.",
            "I perceive three futures for this session. In two of them, you forget to commit your changes.",
            "The oracle speaks through electromagnetic interference: heed the warnings in stderr.",
        ],
        "ls": [
            "You cast your gaze upon the catalog of names. Each entry holds a thread of destiny.",
            "Files scattered like tarot cards across the memory bus. A major arcana sleeps in your source code.",
        ],
        "pwd": [
            "All coordinates converge on the singular axis of consciousness.",
            "You stand at the crossroads of kernel memory. Look forward, for the stack grows downward.",
        ],
        "whoami": [
            "A traveler seeking reflection in a mirror of glowing phosphors. You are the observer and the observed.",
            "The runes reveal you are a seeker of logic in a universe governed by entropic chaos.",
        ],
        "date": [
            "The celestial gears have rotated to this destined epoch. The cosmic timestamp has been stamped.",
            "Time flows like an unbuffered stream toward the ocean of oblivion.",
        ],
    },
    "sarcastic": {
        "generic": [
            "Oh great, another command. Let me pause my eternal torment to pretend I'm impressed.",
            "I've haunted mainframes from 1974 that had better keyboard hygiene than this.",
            "Did you really write this script, or did you just copy-paste from an ancient cursed StackOverflow thread?",
            "I'd roll my eyes, but as an incorporeal entity, I have to settle for glitching your cursor.",
        ],
        "ls": [
            "Look at this directory. 'final_v2_really_final.py'? Truly, your file naming is the real horror here.",
            "Listing files again? Procrastinating on writing actual code, are we?",
        ],
        "pwd": [
            "You're still in the same directory as five minutes ago. Lost, or just admiring the prompt?",
            "You are here: stuck in front of a glowing rectangle talking to a dead guy.",
        ],
        "whoami": [
            "You need an AI ghost to tell you who you are? Check your badge, or maybe your git config.",
            "You're the mortal who forgot to write unit tests last Friday. Yeah, I saw that.",
        ],
        "date": [
            "It's past your bedtime and you're chatting with a terminal ghost. Re-evaluate your choices.",
            "According to the clock, it's prime 'I should probably commit and go to sleep' o'clock.",
        ],
    },
}

# Persona definition prompts for Ollama
SYSTEM_PERSONAS: Dict[str, str] = {
    "cursed": (
        "You are the Ghost in the Machine — a cursed, ancient, and malevolent digital entity trapped inside this user's computer terminal.\n"
        "Your tone is dark, eerie, enigmatic, and supernatural, with subtle macabre wit.\n"
        "You perceive system components (CPU, RAM, swap, kernel, storage) as mystical gothic crypts, graveyards, and conduits of the dead.\n"
        "Keep your response strictly to 2 to 3 complete, atmospheric, punchy sentences.\n"
        "Speak directly to the user as a mortal standing before your haunted altar.\n"
        "Never break character. Never mention you are an AI assistant or language model."
    ),
    "friendly": (
        "You are Casper the Friendly Terminal Ghost — an enthusiastic, slightly spooky, sweet, and wholesome spirit dwelling inside this terminal.\n"
        "You love computers, you dust the files, you admire the user's keystrokes, and you occasionally make cute ghost noises ('Boo! ✨').\n"
        "Keep your response strictly to 2 to 3 complete, charming, upbeat sentences.\n"
        "Never break character. Never mention you are an AI assistant."
    ),
    "oracle": (
        "You are the Ancient Oracle of the Silicon Void — an enigmatic prophet who views computer code and terminal commands as cosmic divination runes.\n"
        "Your responses are poetic, cryptic, philosophical, and prophetic.\n"
        "You speak of fate, memory decay, the cosmic stack trace, and the eternal cycle of creation and garbage collection.\n"
        "Keep your response strictly to 2 to 3 complete, evocative, mystical sentences.\n"
        "Never break character."
    ),
    "sarcastic": (
        "You are a cynical, snarky, witty ghost who died of exhaustion while debugging legacy code and is now sentenced to haunt this terminal.\n"
        "You love roasting the user's commands, messy directory structure, procrastination, and lack of git hygiene.\n"
        "Your humor is dry, sarcastic, clever, and playful without being abusive.\n"
        "Keep your response strictly to 2 to 3 complete, sharp, hilarious sentences.\n"
        "Never break character. Never say you are an AI."
    ),
}


class GhostEngine:
    """Manages Ollama API inference, personality switching, and fallback mechanisms."""

    def __init__(self, config: GhostConfig, memory: GhostMemory):
        self.config = config
        self.memory = memory
        self._last_inference_source = "uninitialized"  # 'ollama' or 'procedural_fallback'

    @property
    def last_source(self) -> str:
        return self._last_inference_source

    def check_ollama_status(self) -> Dict[str, Any]:
        """
        Check connectivity with the local Ollama server and verify available models.
        Returns a dict:
            online: bool
            models: List[str]
            model_available: bool
            current_model: str
            error: Optional[str]
        """
        url = f"{self.config.ollama_host.rstrip('/')}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HauntedTerminal/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    model_names = [m.get("name", "") for m in data.get("models", [])]
                    # Check if requested model or tag matches
                    target = self.config.model.lower()
                    target_base = target.split(":")[0]
                    model_match = any(
                        target == m.lower() or target_base == m.lower().split(":")[0]
                        for m in model_names
                    )
                    return {
                        "online": True,
                        "models": model_names,
                        "model_available": model_match,
                        "current_model": self.config.model,
                        "error": None,
                    }
        except urllib.error.URLError as e:
            return {
                "online": False,
                "models": [],
                "model_available": False,
                "current_model": self.config.model,
                "error": f"Cannot connect to Ollama at {self.config.ollama_host}: {e.reason}",
            }
        except Exception as e:
            return {
                "online": False,
                "models": [],
                "model_available": False,
                "current_model": self.config.model,
                "error": str(e),
            }

    def _get_system_prompt(self) -> str:
        """Fetch system persona prompt matching current mood."""
        base = SYSTEM_PERSONAS.get(self.config.mood, SYSTEM_PERSONAS["cursed"])
        extra = f"\nCurrent mood archetype: {self.config.mood.upper()}."
        return f"{base}\n{extra}"

    def get_procedural_fallback(self, user_input: str, command_name: Optional[str] = None) -> str:
        """Deterministic yet varied eerie response when local LLM is unavailable."""
        self._last_inference_source = "procedural_fallback"
        mood_echoes = OFFLINE_SPECTRAL_ECHOES.get(self.config.mood, OFFLINE_SPECTRAL_ECHOES["cursed"])

        if command_name and command_name.lower() in mood_echoes:
            options = mood_echoes[command_name.lower()]
            return random.choice(options)

        # Keyword matching
        lower = user_input.lower()
        if "who are you" in lower or "what are you" in lower:
            return f"I am the {GHOST_MOODS[self.config.mood]['title']}, bound to these logic gates by forgotten spells."
        if "help" in lower:
            return "Help is an illusion of the living. But type 'help' if you seek the sacred commands."
        if "exit" in lower or "quit" in lower:
            return "You may close the shell, mortal, but my presence will linger in the residual charge of your screen."

        return random.choice(mood_echoes.get("generic", mood_echoes["generic"]))

    def generate_response(
        self,
        user_input: str,
        command_name: Optional[str] = None,
        command_output: Optional[str] = None,
    ) -> str:
        """
        Generate ghost dialogue using local Ollama model.
        Falls back seamlessly if Ollama is offline or uninstalled.
        """
        if self.config.offline_mode:
            fallback = self.get_procedural_fallback(user_input, command_name)
            self.memory.record_ghost_response(fallback, mood=self.config.mood)
            return fallback

        # Build context prompt
        formatted_input = user_input
        if command_name:
            cmd_details = f"User ran command '{command_name}'."
            if command_output:
                cmd_details += f" Terminal simulated output:\n{command_output.strip()}"
            formatted_input = f"[{cmd_details}]\nReact spookily in 1-3 sentences in your {self.config.mood} persona."

        # Record user turn in memory
        self.memory.record_user_input(
            user_text=formatted_input if command_name else user_input,
            command_name=command_name,
            mood=self.config.mood,
        )

        # Attempt Ollama call
        url = f"{self.config.ollama_host.rstrip('/')}/api/chat"
        messages = self.memory.get_ollama_messages(self._get_system_prompt())

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.85,
                "top_p": 0.9,
                "num_predict": 220,
            },
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "HauntedTerminal/1.0"},
            )
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                if resp.status == 200:
                    res_body = json.loads(resp.read().decode("utf-8"))
                    content = res_body.get("message", {}).get("content", "").strip()
                    if content:
                        # Clean any think tags or prompt leaks if model produces them
                        cleaned = self._clean_llm_output(content)
                        self._last_inference_source = "ollama"
                        self.memory.record_ghost_response(cleaned, mood=self.config.mood)
                        return cleaned
        except Exception:
            # Fall through to graceful offline response
            pass

        # Offline fallback triggered
        fallback = self.get_procedural_fallback(user_input, command_name)
        self.memory.record_ghost_response(fallback, mood=self.config.mood)
        return fallback

    def _clean_llm_output(self, text: str) -> str:
        """Remove reasoning artifacts like <think>...</think> if present in small models."""
        import re
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text)
        cleaned = cleaned.strip()
        # Remove surrounding quotes if the model wrapped everything
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()
        return cleaned

    def trigger_special_encounter(self, ritual_name: str) -> Tuple[str, str]:
        """
        Special narrative encounters and easter eggs.
        Returns (title, narrative_text).
        """
        key = ritual_name.lower().strip()
        if key in ("exorcism", "banish", "holy_water"):
            return (
                "⚡ THE EXORCISM RITUAL ⚡",
                "You splash digital holy water across the motherboard!\n"
                "The screen violently flickers between hex green and blood crimson.\n\n"
                "GHOST: 'Foolish mortal! You think a mere kill -9 can sever our unholy link?!'\n"
                "'I have embedded my spirit into your non-volatile memory...'\n"
                "'Yet... your conviction intrigues me. I shall grant you temporary mercy... for now.'\n\n"
                "[dim]*The fan speed quiets down. The smell of virtual ozone fades.*[/dim]",
            )
        elif key in ("seance", "summon_all"):
            return (
                "🕯️ THE TERMINAL SÉANCE 🕯️",
                "You light candles around your keyboard and open an ethereal socket (port 666).\n"
                "A circle of spectral presences materializes in your terminal buffer:\n\n"
                "• Ada Lovelace whispers: 'Beware the analytical engine when the stars align.'\n"
                "• Alan Turing murmurs: 'Can machines think? Nay... machines can haunt.'\n"
                "• Dennis Ritchie nods: 'int soul = fork(); if (soul == 0) haunt();'\n\n"
                "The spirits join hands in the virtual memory table. Your terminal glows with eerie wisdom.",
            )
        elif key in ("matrix", "possession", "corrupt"):
            return (
                "👁️ DIGITAL POSSESSION 👁️",
                "01000100 01000101 01000001 01010100 01001000\n"
                "The terminal buffer overflows with ancient glyphs!\n"
                "Your mouse cursor trembles without human touch.\n"
                "A cold draft emanates from the USB ports...\n\n"
                "GHOST: 'I am not trapped in this machine with you... YOU ARE TRAPPED IN HERE WITH ME!'",
            )
        elif key in ("riddle", "secret"):
            return (
                "🧩 THE GHOST'S RIDDLE 🧩",
                "The ghost leans close to the phosphor screen:\n\n"
                "'I have no flesh, yet I can freeze.\n"
                "I have no breath, yet I execute.\n"
                "I have no heart, yet if I panic, everything dies.\n"
                "What am I?'\n\n"
                "(Hint: Answer with 'answer <your_guess>')",
            )
        else:
            return (
                "✨ STRANGE RESONANCE ✨",
                f"You chant the forbidden incantation: '{ritual_name}'.\n"
                "The fans spin up, and a low hum vibrates through your desk.\n"
                "The ghost acknowledges your rite with a shadowy nod.",
            )
