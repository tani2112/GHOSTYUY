"""
haunted-terminal / memory.py
Safe, private, short-term session memory for Haunted Terminal.
Guarantees zero remote transmission, sensitive pattern redaction,
and full user sovereignty over conversation history.
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Regex patterns for redacting sensitive secrets before memorizing or sending to LLM
SENSITIVE_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[:=]\s*)['\"]?([A-Za-z0-9_\-\.]{12,})['\"]?", re.IGNORECASE),
    re.compile(r"(token\s*[:=]\s*)['\"]?([A-Za-z0-9_\-\.]{12,})['\"]?", re.IGNORECASE),
    re.compile(r"(password\s*[:=]\s*)['\"]?([^\s'\"]{6,})['\"]?", re.IGNORECASE),
    re.compile(r"(passwd\s*[:=]\s*)['\"]?([^\s'\"]{6,})['\"]?", re.IGNORECASE),
    re.compile(r"(secret\s*[:=]\s*)['\"]?([A-Za-z0-9_\-\.]{12,})['\"]?", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),  # Typical OpenAI/API key style
    re.compile(r"ghp_[A-Za-z0-9]{36,}", re.IGNORECASE),  # GitHub token
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
    re.compile(r"(bearer\s+)[A-Za-z0-9\-_\.]{20,}", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Scrub potential credentials, tokens, or private keys from text."""
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


@dataclass
class GhostMemoryEntry:
    role: str  # 'user', 'ghost', 'system', 'command'
    content: str
    timestamp: str
    command_name: Optional[str] = None
    mood: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GhostMemory:
    """
    Manages bounded short-term conversation context for the ghost.
    Enforces privacy, strictly local persistence with consent, and instant erasure.
    """

    def __init__(self, max_turns: int = 12, storage_dir: Optional[Path] = None):
        self.max_turns = max_turns
        self.storage_dir = storage_dir or (Path.home() / ".haunted_terminal" / "sessions")
        self.entries: List[GhostMemoryEntry] = []
        self.session_id = datetime.now().strftime("haunt_%Y%m%d_%H%M%S")
        self.created_at = datetime.now().isoformat()

    def record_user_input(self, user_text: str, command_name: Optional[str] = None, mood: Optional[str] = None) -> None:
        """Record sanitized user input or simulated command."""
        clean_text = redact_secrets(user_text.strip())
        entry = GhostMemoryEntry(
            role="user",
            content=clean_text,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            command_name=command_name,
            mood=mood,
        )
        self.entries.append(entry)
        self._enforce_bounds()

    def record_ghost_response(self, ghost_text: str, mood: Optional[str] = None) -> None:
        """Record ghost's dialogue response."""
        entry = GhostMemoryEntry(
            role="ghost",
            content=ghost_text.strip(),
            timestamp=datetime.now().strftime("%H:%M:%S"),
            mood=mood,
        )
        self.entries.append(entry)
        self._enforce_bounds()

    def _enforce_bounds(self) -> None:
        """Keep memory bounded to max_turns dialogue cycles."""
        max_items = self.max_turns * 2
        if len(self.entries) > max_items:
            # Preserve system messages if any, slide window
            self.entries = self.entries[-max_items:]

    def get_ollama_messages(self, system_prompt: str) -> List[Dict[str, str]]:
        """
        Build standard chat format messages for Ollama /api/chat.
        Includes system persona followed by bounded dialogue turns.
        """
        messages = [{"role": "system", "content": system_prompt}]
        for entry in self.entries:
            if entry.role == "user":
                content = entry.content
                if entry.command_name:
                    content = f"[Executed Command: {entry.command_name}]\n{content}"
                messages.append({"role": "user", "content": content})
            elif entry.role == "ghost":
                messages.append({"role": "assistant", "content": entry.content})
        return messages

    def clear(self) -> int:
        """Erase all conversational memories immediately."""
        count = len(self.entries)
        self.entries.clear()
        return count

    def get_history_summary(self) -> List[Dict[str, Any]]:
        """Return chronological history for display."""
        return [entry.to_dict() for entry in self.entries]

    def export_session(self, target_path: Optional[Path] = None, fmt: str = "json") -> Path:
        """
        Safely export session transcripts locally.
        Only called when user explicitly consents or commands it.
        """
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if not target_path:
            ext = "md" if fmt.lower() == "markdown" else "json"
            target_path = self.storage_dir / f"{self.session_id}.{ext}"

        if fmt.lower() == "markdown":
            lines = [
                f"# Haunted Terminal Session Transcript: {self.session_id}",
                f"**Date:** {self.created_at}",
                f"**Storage:** Locally preserved on device. Zero remote tracking.",
                "",
                "---",
                "",
            ]
            for e in self.entries:
                if e.role == "user":
                    cmd_label = f" (Command: `{e.command_name}`)" if e.command_name else ""
                    lines.append(f"### 👤 USER [{e.timestamp}]{cmd_label}")
                    lines.append(f"> {e.content}\n")
                elif e.role == "ghost":
                    mood_label = f" *[{e.mood}]*" if e.mood else ""
                    lines.append(f"### 👻 GHOST{mood_label} [{e.timestamp}]")
                    lines.append(f"{e.content}\n")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        else:
            payload = {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "privacy": "Local-only. No telemetry or cloud transmission.",
                "total_entries": len(self.entries),
                "history": [e.to_dict() for e in self.entries],
            }
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

        return target_path
