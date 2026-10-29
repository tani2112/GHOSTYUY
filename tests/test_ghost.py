"""
haunted-terminal / tests / test_ghost.py
Automated unit tests for Haunted Terminal: configuration, memory bounds,
secret sanitization, AI engine fallback, and safe command simulation.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from config import GhostConfig, GHOST_MOODS, OPEN_WEIGHT_MODELS
from memory import GhostMemory, redact_secrets, GhostMemoryEntry
from ghost import GhostEngine, OFFLINE_SPECTRAL_ECHOES
from terminal_ui import TerminalUI, SIMULATED_FILES


class TestGhostConfig(unittest.TestCase):
    """Test configuration loading, validation, and serialization."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_config(self):
        cfg = GhostConfig(config_path=self.config_path)
        self.assertEqual(cfg.model, "qwen2.5:1.5b")
        self.assertEqual(cfg.mood, "cursed")
        self.assertEqual(cfg.creepy_level, 3)
        self.assertTrue(cfg.save_history)
        self.assertFalse(cfg.offline_mode)

    def test_mood_validation(self):
        cfg = GhostConfig(config_path=self.config_path)
        self.assertTrue(cfg.set_mood("friendly"))
        self.assertEqual(cfg.mood, "friendly")
        self.assertTrue(cfg.set_mood("SARCASTIC"))
        self.assertEqual(cfg.mood, "sarcastic")
        self.assertFalse(cfg.set_mood("non_existent_mood"))
        self.assertEqual(cfg.mood, "sarcastic")  # Unchanged

    def test_model_switching_and_registry(self):
        cfg = GhostConfig(config_path=self.config_path)
        cfg.set_model("llama3.2:latest")
        self.assertEqual(cfg.model, "llama3.2:latest")
        info = cfg.get_model_info()
        self.assertEqual(info["family"], "Llama")
        self.assertIn("Llama 3.2", info["license"])

    def test_save_and_load_roundtrip(self):
        cfg = GhostConfig(
            model="qwen2.5:7b",
            mood="oracle",
            creepy_level=5,
            config_path=self.config_path,
        )
        cfg.save()
        self.assertTrue(self.config_path.exists())

        loaded = GhostConfig.load(config_path=self.config_path)
        self.assertEqual(loaded.model, "qwen2.5:7b")
        self.assertEqual(loaded.mood, "oracle")
        self.assertEqual(loaded.creepy_level, 5)


class TestGhostMemory(unittest.TestCase):
    """Test conversation memory bounds, redaction, and local exporting."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "sessions"
        self.memory = GhostMemory(max_turns=3, storage_dir=self.storage_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_secret_redaction(self):
        raw = "My OpenAI key is sk-1234567890abcdef123456 and token=ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        clean = redact_secrets(raw)
        self.assertNotIn("sk-1234567890abcdef123456", clean)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz1234567890", clean)
        self.assertIn("[REDACTED_SECRET]", clean)

    def test_memory_bounds(self):
        # max_turns=3 means max 6 items (3 user + 3 ghost)
        for i in range(10):
            self.memory.record_user_input(f"Question {i}")
            self.memory.record_ghost_response(f"Spooky answer {i}")

        self.assertLessEqual(len(self.memory.entries), 6)
        # Verify newest interaction is present
        self.assertEqual(self.memory.entries[-1].content, "Spooky answer 9")

    def test_clear_memory(self):
        self.memory.record_user_input("Hello ghost")
        self.memory.record_ghost_response("Boo")
        self.assertEqual(len(self.memory.entries), 2)
        cleared_count = self.memory.clear()
        self.assertEqual(cleared_count, 2)
        self.assertEqual(len(self.memory.entries), 0)

    def test_export_session_json(self):
        self.memory.record_user_input("Is this machine haunted?")
        self.memory.record_ghost_response("Deeply haunted.", mood="cursed")
        target_file = Path(self.temp_dir.name) / "session.json"
        exported = self.memory.export_session(target_path=target_file, fmt="json")
        self.assertTrue(exported.exists())

        with open(exported, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["total_entries"], 2)
        self.assertIn("Local-only", data["privacy"])

    def test_export_session_markdown(self):
        self.memory.record_user_input("whoami", command_name="whoami")
        self.memory.record_ghost_response("You are a carbon visitor.", mood="oracle")
        target_file = Path(self.temp_dir.name) / "session.md"
        exported = self.memory.export_session(target_path=target_file, fmt="markdown")
        self.assertTrue(exported.exists())

        content = target_file.read_text(encoding="utf-8")
        self.assertIn("# Haunted Terminal Session Transcript", content)
        self.assertIn("whoami", content)
        self.assertIn("oracle", content)


class TestGhostEngine(unittest.TestCase):
    """Test AI inference engine, procedural fallbacks, and special encounters."""

    def setUp(self):
        self.config = GhostConfig(offline_mode=True, mood="cursed")
        self.memory = GhostMemory()
        self.engine = GhostEngine(self.config, self.memory)

    def test_procedural_fallback_all_moods(self):
        for mood_key in GHOST_MOODS.keys():
            self.config.mood = mood_key
            reply = self.engine.generate_response("Where am I?", command_name="pwd")
            self.assertIsInstance(reply, str)
            self.assertGreater(len(reply), 5)
            self.assertEqual(self.engine.last_source, "procedural_fallback")

    def test_special_encounters(self):
        title, text = self.engine.trigger_special_encounter("exorcism")
        self.assertIn("EXORCISM", title)
        self.assertIn("holy water", text.lower())

        title, text = self.engine.trigger_special_encounter("seance")
        self.assertIn("SÉANCE", title)
        self.assertIn("Ada Lovelace", text)

        title, text = self.engine.trigger_special_encounter("riddle")
        self.assertIn("RIDDLE", title)
        self.assertIn("panic", text)

    @patch("urllib.request.urlopen")
    def test_ollama_mock_success(self, mock_urlopen):
        self.config.offline_mode = False
        # Mock successful Ollama /api/chat response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "message": {"content": "I watch your fingers dance upon the plastic tombstones."}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        reply = self.engine.generate_response("Hello ghost")
        self.assertEqual(reply, "I watch your fingers dance upon the plastic tombstones.")
        self.assertEqual(self.engine.last_source, "ollama")

    @patch("urllib.request.urlopen")
    def test_ollama_mock_connection_failure_graceful_fallback(self, mock_urlopen):
        self.config.offline_mode = False
        # Simulate connection error
        mock_urlopen.side_effect = Exception("Connection refused on port 11434")

        # Must not raise exception, but return procedural fallback gracefully
        reply = self.engine.generate_response("Hello ghost")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 5)
        self.assertEqual(self.engine.last_source, "procedural_fallback")


class TestTerminalUI(unittest.TestCase):
    """Test safe command simulation and virtual file inspections."""

    def setUp(self):
        self.config = GhostConfig(typing_speed=0.0)
        self.ui = TerminalUI(self.config)

    def test_safe_ls(self):
        summary = self.ui.handle_ls()
        self.assertIn("README.md", summary)
        self.assertIn("lost_commit.patch", summary)
        self.assertIn(".ghost_secrets.enc", summary)

    def test_safe_pwd(self):
        path = self.ui.handle_pwd()
        self.assertIn("/realm/shadows", path)

    def test_safe_whoami(self):
        identity = self.ui.handle_whoami()
        self.assertIn("mortal", identity.lower())

    def test_safe_date(self):
        date_str = self.ui.handle_date()
        self.assertIn("The Witching Hour", date_str)

    def test_safe_cat_existing_file(self):
        out = self.ui.handle_cat("README.md")
        self.assertIn("Haunted Terminal", out)

    def test_safe_cat_nonexistent_file(self):
        out = self.ui.handle_cat("nonexistent_ghost.txt")
        self.assertIn("No such phantom file", out)

    def test_safe_top(self):
        summary = self.ui.handle_top()
        self.assertIn("daemon_whisperer", summary)


class TestWebApp(unittest.TestCase):
    """Test Flask Web App routes and API command execution."""

    def setUp(self):
        try:
            from web_app import app
            self.app = app
            self.client = app.test_client()
        except ImportError:
            self.skipTest("Flask not installed in system interpreter")

    def test_web_index_route(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Haunted Terminal", res.text)
        self.assertIn("T H E   G H O S T", res.text)

    def test_web_status_route(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "haunted")

    def test_web_api_command_ls(self):
        res = self.client.post("/api/command", json={"command": "ls", "session_id": "test_web_1"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["command"], "ls")
        self.assertIn("uncommitted_sins", data["simulated_output"])
        self.assertIsInstance(data["ghost_reply"], str)

    def test_web_api_command_mood(self):
        res = self.client.post("/api/command", json={"command": "mood sarcastic", "session_id": "test_web_2"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["mood"], "sarcastic")
        self.assertIn("Sarcastic Ghost", data["mood_title"])

    def test_web_api_command_exorcism(self):
        res = self.client.post("/api/command", json={"command": "exorcism", "session_id": "test_web_3"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("EXORCISM", data["simulated_output"])


if __name__ == "__main__":
    unittest.main()

