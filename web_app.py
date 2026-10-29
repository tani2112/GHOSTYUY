"""
haunted-terminal / web_app.py
Production-ready Web Terminal for Render deployment and browser interactions.
Serves a retro-gothic CRT terminal interface and REST API for Haunted Terminal.
"""

import os
import json
import uuid
import time
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template_string

from config import GhostConfig, GHOST_MOODS, OPEN_WEIGHT_MODELS
from memory import GhostMemory
from ghost import GhostEngine
from terminal_ui import SIMULATED_FILES

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "haunted_secret_key_666")

# In-memory session store mapping session_id -> (GhostConfig, GhostMemory, GhostEngine)
SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Retrieve or initialize independent session state for each browser visitor."""
    now = time.time()
    # Clean up stale sessions older than 2 hours
    stale_keys = [
        k for k, v in SESSIONS.items() if now - v.get("last_active", now) > 7200
    ]
    for k in stale_keys:
        SESSIONS.pop(k, None)

    if session_id not in SESSIONS:
        cfg = GhostConfig.load()
        # If Render environment provides custom model or host
        if os.environ.get("OLLAMA_HOST"):
            cfg.ollama_host = os.environ.get("OLLAMA_HOST")
        if os.environ.get("GHOST_MOOD"):
            cfg.set_mood(os.environ.get("GHOST_MOOD"))

        mem = GhostMemory()
        engine = GhostEngine(cfg, mem)
        SESSIONS[session_id] = {
            "config": cfg,
            "memory": mem,
            "engine": engine,
            "last_active": now,
        }
    else:
        SESSIONS[session_id]["last_active"] = now

    return SESSIONS[session_id]


# --- Web Terminal HTML / CSS / JS Template ---
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👻 Haunted Terminal — The Ghost That Lives in Your Computer</title>
    <meta name="description" content="An interactive AI ghost possessing your terminal. Powered by open-weight AI and deployed on Render.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Creepster&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #08080c;
            --screen-bg: #0d0f14;
            --text-color: #00ff88;
            --ghost-color: #39ff14;
            --accent-purple: #9d4edd;
            --accent-red: #ff0055;
            --accent-cyan: #00f0ff;
            --accent-yellow: #ffbe0b;
            --glow: 0 0 10px rgba(0, 255, 136, 0.45);
            --font-mono: 'Fira Code', 'Courier New', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-mono);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 50% 20%, rgba(157, 78, 221, 0.12) 0%, transparent 60%),
                radial-gradient(circle at 80% 80%, rgba(255, 0, 85, 0.08) 0%, transparent 50%);
        }

        /* Top Header Bar */
        .top-bar {
            width: 100%;
            max-width: 1100px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 16px;
            background: rgba(18, 18, 26, 0.85);
            border: 1px solid rgba(157, 78, 221, 0.3);
            border-radius: 8px;
            backdrop-filter: blur(8px);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1rem;
            font-weight: 700;
            color: #fff;
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
        }

        .badges {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }

        .badge {
            font-size: 0.72rem;
            padding: 4px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .badge-render {
            background: #46e3b7;
            color: #000;
        }

        .badge-status {
            background: rgba(0, 255, 136, 0.15);
            color: #00ff88;
            border: 1px solid #00ff88;
        }

        .audio-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #aaa;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            font-family: inherit;
            transition: all 0.2s;
        }
        .audio-btn:hover {
            color: #fff;
            border-color: var(--accent-cyan);
        }

        /* CRT Terminal Frame */
        .crt-frame {
            position: relative;
            width: 100%;
            max-width: 1100px;
            background: #11131a;
            border: 2px solid #2a2d3d;
            border-radius: 12px;
            box-shadow: 
                0 0 30px rgba(0, 0, 0, 0.8),
                0 0 15px rgba(157, 78, 221, 0.25),
                inset 0 0 15px rgba(0, 0, 0, 0.9);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* Scanline Overlay */
        .crt-frame::before {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            z-index: 20;
            background-size: 100% 3px, 6px 100%;
            pointer-events: none;
            opacity: 0.6;
        }

        .terminal-header {
            background: #181a24;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #2a2d3d;
            z-index: 25;
        }

        .window-dots {
            display: flex;
            gap: 6px;
        }

        .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .dot-red { background: #ff5f56; }
        .dot-yellow { background: #ffbd2e; }
        .dot-green { background: #27c93f; }

        .terminal-title {
            font-size: 0.82rem;
            color: #888;
            font-weight: 600;
        }

        /* Screen Output Area */
        .terminal-body {
            background-color: var(--screen-bg);
            padding: 20px;
            min-height: 480px;
            max-height: 60vh;
            overflow-y: auto;
            position: relative;
            z-index: 10;
            scroll-behavior: smooth;
        }

        .terminal-body::-webkit-scrollbar {
            width: 8px;
        }
        .terminal-body::-webkit-scrollbar-thumb {
            background: #2a2d3d;
            border-radius: 4px;
        }

        .banner-pre {
            font-size: 0.72rem;
            line-height: 1.15;
            color: var(--text-color);
            text-shadow: var(--glow);
            margin-bottom: 16px;
            white-space: pre;
            overflow-x: auto;
        }

        .line {
            margin-bottom: 12px;
            line-height: 1.5;
            word-break: break-word;
        }

        .prompt-line {
            color: #fff;
            display: flex;
            gap: 8px;
            align-items: baseline;
        }

        .prompt-symbol {
            color: var(--ghost-color);
            font-weight: bold;
        }

        .cmd-text {
            color: #fff;
            font-weight: 600;
        }

        .ghost-response-container {
            margin-top: 6px;
            margin-bottom: 14px;
            padding: 12px 16px;
            background: rgba(20, 24, 34, 0.7);
            border-left: 3px solid var(--ghost-color);
            border-radius: 0 6px 6px 0;
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.4);
        }

        .ghost-header {
            font-size: 0.82rem;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            color: var(--ghost-color);
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.4);
        }

        .source-tag {
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.1);
            color: #ccc;
            font-weight: normal;
        }

        .ghost-content {
            color: #e0e0e0;
            font-size: 0.94rem;
            line-height: 1.5;
        }

        .simulated-output {
            color: #a0aec0;
            font-size: 0.86rem;
            background: rgba(0, 0, 0, 0.35);
            padding: 8px 12px;
            border-radius: 4px;
            margin-top: 6px;
            margin-bottom: 8px;
            white-space: pre-wrap;
            border: 1px dashed rgba(255, 255, 255, 0.15);
        }

        /* Input Controls */
        .terminal-input-bar {
            background: #141620;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            border-top: 1px solid #2a2d3d;
            gap: 10px;
            z-index: 25;
        }

        .cli-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-family: var(--font-mono);
            font-size: 1rem;
            font-weight: 600;
            caret-color: var(--text-color);
        }

        .submit-btn {
            background: linear-gradient(135deg, #9d4edd, #ff0055);
            border: none;
            color: #fff;
            padding: 8px 16px;
            font-family: inherit;
            font-weight: bold;
            font-size: 0.85rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .submit-btn:hover {
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
        }

        /* Quick Commands Pill Tray */
        .pill-tray {
            width: 100%;
            max-width: 1100px;
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .pill {
            background: rgba(26, 28, 40, 0.8);
            border: 1px solid rgba(157, 78, 221, 0.3);
            color: #c77dff;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            padding: 6px 12px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .pill:hover {
            background: rgba(157, 78, 221, 0.25);
            color: #fff;
            border-color: var(--accent-cyan);
            transform: translateY(-2px);
        }

        /* Footer */
        footer {
            margin-top: 16px;
            font-size: 0.75rem;
            color: #666;
            text-align: center;
        }
        footer a {
            color: var(--accent-cyan);
            text-decoration: none;
        }
    </style>
</head>
<body>

    <!-- Top Status Bar -->
    <header class="top-bar">
        <div class="brand">
            <span>👻</span> Haunted Terminal
        </div>
        <div class="badges">
            <span class="badge badge-render">🚀 Deployed on Render</span>
            <span class="badge badge-status" id="model-badge">Open-Weight AI</span>
            <button class="audio-btn" id="audio-toggle" onclick="toggleAudio()">🔊 Sound: ON</button>
        </div>
    </header>

    <!-- CRT Screen Frame -->
    <main class="crt-frame">
        <div class="terminal-header">
            <div class="window-dots">
                <div class="dot dot-red"></div>
                <div class="dot dot-yellow"></div>
                <div class="dot dot-green"></div>
            </div>
            <div class="terminal-title">ghost@haunted-machine: ~ (v1.0.0-render)</div>
            <div style="width: 50px;"></div>
        </div>

        <section class="terminal-body" id="terminal-body" aria-label="Terminal Screen">
            <pre class="banner-pre">
 ██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
 ██║  ██║██╔══██╗██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
 ███████║███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██║  ██║
 ██╔══██║██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║  ██║
 ██║  ██║██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═════╝ 
        👻 T H E   G H O S T   I N   T H E   M A C H I N E 👻
            </pre>
            <div class="line" style="color: #00ff88;">
                [+] The spectral entity has possessed this cloud container.<br>
                [+] Open-Weight Neural Core initialized &amp; ready.<br>
                [+] Type <strong>'help'</strong> for sacred commands, or speak directly to the phantom.
            </div>
            <div id="output-anchor"></div>
        </section>

        <form class="terminal-input-bar" onsubmit="submitCommand(event)">
            <span class="prompt-symbol" id="current-prompt">💀 [cursed@haunted-machine ~]$</span>
            <input type="text" id="cli-input" class="cli-input" autocomplete="off" spellcheck="false" placeholder="Type 'ls', 'whoami', 'exorcism', or ask anything..." autofocus>
            <button type="submit" class="submit-btn">EXECUTE</button>
        </form>
    </main>

    <!-- Quick Pill Tray for Mobile and Fast Exploration -->
    <nav class="pill-tray" aria-label="Quick Commands">
        <button type="button" class="pill" onclick="runPill('ls')">📁 ls</button>
        <button type="button" class="pill" onclick="runPill('whoami')">👤 whoami</button>
        <button type="button" class="pill" onclick="runPill('pwd')">📍 pwd</button>
        <button type="button" class="pill" onclick="runPill('cat souls.db')">📜 cat souls.db</button>
        <button type="button" class="pill" onclick="runPill('top')">☠ top</button>
        <button type="button" class="pill" onclick="runPill('mood sarcastic')">😏 mood sarcastic</button>
        <button type="button" class="pill" onclick="runPill('mood friendly')">✨ mood friendly</button>
        <button type="button" class="pill" onclick="runPill('mood oracle')">🔮 mood oracle</button>
        <button type="button" class="pill" onclick="runPill('exorcism')">⚡ exorcism</button>
        <button type="button" class="pill" onclick="runPill('seance')">🕯️ seance</button>
        <button type="button" class="pill" onclick="runPill('riddle')">🧩 riddle</button>
        <button type="button" class="pill" onclick="runPill('help')">📖 help</button>
        <button type="button" class="pill" onclick="runPill('status')">📊 status</button>
    </nav>

    <footer>
        Haunted Terminal • Built for Hacktoberfest 2026: Ghost in the Machine • 
        <a href="https://github.com/tani2112/GHOSTYUY" target="_blank" rel="noopener">GitHub Repository</a> • 
        Hosted on <a href="https://render.com" target="_blank" rel="noopener">Render</a>
    </footer>

    <script>
        // Web Audio Synthesizer for Ghost Sound Effects
        let audioEnabled = true;
        let audioCtx = null;

        function initAudio() {
            if (!audioCtx) {
                try {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                } catch(e) {}
            }
        }

        function playKeyClick() {
            if (!audioEnabled || !audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(400 + Math.random() * 200, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.015, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.05);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.05);
        }

        function playGhostChime() {
            if (!audioEnabled || !audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(220, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(110, audioCtx.currentTime + 0.4);
            gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.4);
        }

        function toggleAudio() {
            audioEnabled = !audioEnabled;
            document.getElementById('audio-toggle').innerText = audioEnabled ? '🔊 Sound: ON' : '🔇 Sound: OFF';
            if (audioEnabled) initAudio();
        }

        // Session ID management
        let sessionId = localStorage.getItem('haunted_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Math.random().toString(36).substring(2, 12);
            localStorage.setItem('haunted_session_id', sessionId);
        }

        // Command History Navigation
        const commandHistory = [];
        let historyIndex = -1;
        const cliInput = document.getElementById('cli-input');
        const terminalBody = document.getElementById('terminal-body');
        const outputAnchor = document.getElementById('output-anchor');
        const promptLabel = document.getElementById('current-prompt');

        cliInput.addEventListener('keydown', (e) => {
            initAudio();
            playKeyClick();
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    cliInput.value = commandHistory[commandHistory.length - 1 - historyIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    cliInput.value = commandHistory[commandHistory.length - 1 - historyIndex];
                } else if (historyIndex === 0) {
                    historyIndex = -1;
                    cliInput.value = '';
                }
            }
        });

        function runPill(cmd) {
            cliInput.value = cmd;
            submitCommand(new Event('submit'));
        }

        async function submitCommand(e) {
            if (e) e.preventDefault();
            initAudio();
            const raw = cliInput.value.trim();
            if (!raw) return;

            commandHistory.push(raw);
            historyIndex = -1;
            cliInput.value = '';

            if (raw.toLowerCase() === 'clear') {
                const lines = terminalBody.querySelectorAll('.user-turn, .ghost-response-container');
                lines.forEach(l => l.remove());
                return;
            }

            // Print User Prompt line
            const userTurn = document.createElement('div');
            userTurn.className = 'line user-turn';
            userTurn.innerHTML = `
                <div class="prompt-line">
                    <span class="prompt-symbol">${promptLabel.innerText}</span>
                    <span class="cmd-text">${escapeHtml(raw)}</span>
                </div>
            `;
            outputAnchor.before(userTurn);
            terminalBody.scrollTop = terminalBody.scrollHeight;

            // Loading state
            const loadingBox = document.createElement('div');
            loadingBox.className = 'ghost-response-container';
            loadingBox.innerHTML = `
                <div class="ghost-header">👻 The spirit is stirring...</div>
                <div class="ghost-content" style="color: #888;">...reading residual magnetic fields...</div>
            `;
            outputAnchor.before(loadingBox);
            terminalBody.scrollTop = terminalBody.scrollHeight;

            try {
                const res = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: raw, session_id: sessionId })
                });
                const data = await res.json();
                loadingBox.remove();
                renderResponse(data);
                playGhostChime();
            } catch (err) {
                loadingBox.remove();
                const errBox = document.createElement('div');
                errBox.className = 'ghost-response-container';
                errBox.style.borderColor = 'red';
                errBox.innerHTML = `
                    <div class="ghost-header" style="color: red;">⚠️ Spectral Disconnect</div>
                    <div class="ghost-content">The ethereal connection was severed: ${err.message}</div>
                `;
                outputAnchor.before(errBox);
            }
        }

        function renderResponse(data) {
            // Update Prompt Symbol if mood changed
            if (data.prompt_symbol) {
                promptLabel.innerText = data.prompt_symbol;
            }

            const container = document.createElement('div');
            container.className = 'ghost-response-container';
            if (data.accent) container.style.borderLeftColor = data.accent;

            let simulatedHtml = '';
            if (data.simulated_output) {
                simulatedHtml = `<div class="simulated-output">${escapeHtml(data.simulated_output)}</div>`;
            }

            const sourceBadge = data.source === 'ollama' 
                ? '⚡ local neural' 
                : '🍂 spectral procedural';

            container.innerHTML = `
                ${simulatedHtml}
                <div class="ghost-header">
                    <span>👻 GHOST (${escapeHtml(data.mood_title || 'Ghost')}):</span>
                    <span class="source-tag">${sourceBadge}</span>
                </div>
                <div class="ghost-content" id="stream-text-${Date.now()}"></div>
            `;

            outputAnchor.before(container);
            terminalBody.scrollTop = terminalBody.scrollHeight;

            // Typewriter effect for ghost reply
            const textNode = container.querySelector('.ghost-content');
            typewriter(textNode, data.ghost_reply, 0, 16);
        }

        function typewriter(element, text, index, speed) {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                terminalBody.scrollTop = terminalBody.scrollHeight;
                setTimeout(() => typewriter(element, text, index + 1, speed), speed);
            }
        }

        function escapeHtml(str) {
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Serve the interactive web terminal."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/command", methods=["POST"])
def api_command():
    """Handle simulated commands and conversational inquiries from the web terminal."""
    data = request.get_json() or {}
    user_cmd = data.get("command", "").strip()
    session_id = data.get("session_id", "default_guest")

    session = get_or_create_session(session_id)
    cfg: GhostConfig = session["config"]
    engine: GhostEngine = session["engine"]

    if not user_cmd:
        return jsonify({"error": "No command provided"}), 400

    parts = user_cmd.split(maxsplit=1)
    base_cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    simulated_output = None
    ghost_reply = ""
    mood_info = GHOST_MOODS.get(cfg.mood, GHOST_MOODS["cursed"])

    # Safe Command Execution Dispatcher
    if base_cmd in ("ls", "dir"):
        simulated_output = (
            "Permissions  Size    Last Modified   Filename\n"
            "drwx------   4096 B  Midnight 00:00  uncommitted_sins/\n"
            "drwx------   4096 B  Oct 30 00:00    graveyard_cache/\n"
            "-rw-r--r--   142 B   Oct 30 00:01    README.md\n"
            "-rw-r--r--   3.2 KB  Oct 30 00:02    main.py\n"
            "-rw-------   666 B   Friday 13th     .ghost_secrets.enc\n"
            "-rw-r--r--   1.1 KB  A moment ago    lost_commit.patch\n"
            "-rw-r--r--   12.8 KB Ancient epoch   souls.db\n"
            "-rw-r--r--   512 B   Yesterday       notes_from_the_crypt.txt"
        )
        ghost_reply = engine.generate_response(user_cmd, command_name="ls", command_output=simulated_output)

    elif base_cmd == "pwd":
        simulated_output = "/realm/shadows/virtual_memory/sector_666/lost_souls"
        ghost_reply = engine.generate_response(user_cmd, command_name="pwd", command_output=simulated_output)

    elif base_cmd == "whoami":
        simulated_output = "mortal_traveler (UID 1000, GID: 666(spirits), Shell: /bin/haunt)"
        ghost_reply = engine.generate_response(user_cmd, command_name="whoami", command_output=simulated_output)

    elif base_cmd == "date":
        cur_time = time.strftime("%A, %B %d, %Y - %H:%M:%S")
        simulated_output = f"Spectral Epoch: {cur_time} [The Witching Hour]"
        ghost_reply = engine.generate_response(user_cmd, command_name="date", command_output=simulated_output)

    elif base_cmd == "cat":
        if not args:
            simulated_output = "Usage: cat <filename> (e.g. cat souls.db, cat README.md)"
            ghost_reply = "You must specify which vessel of knowledge you seek to unseal."
        elif args in SIMULATED_FILES:
            simulated_output = SIMULATED_FILES[args]
            ghost_reply = engine.generate_response(user_cmd, command_name=f"cat {args}", command_output=simulated_output)
        else:
            simulated_output = f"cat: '{args}': No such phantom file in ethereal directory."
            ghost_reply = "You search for shadows of things that never were."

    elif base_cmd in ("top", "ps"):
        simulated_output = (
            "PID   USER    CPU%   MEM%   TIME    COMMAND\n"
            "666   ghost   66.6%  13.3%  666:00  daemon_whisperer\n"
            "1337  spirit  24.1%   8.4%  13:37   memory_leak_wraith\n"
            "1     kernel   0.1%   0.2%  72:14   init (possessed)\n"
            "777   mortal   5.2%   2.1%  01:22   python3 web_app.py"
        )
        ghost_reply = engine.generate_response(user_cmd, command_name="top", command_output=simulated_output)

    elif base_cmd == "mood":
        if args and cfg.set_mood(args):
            mood_info = GHOST_MOODS.get(cfg.mood, GHOST_MOODS["cursed"])
            simulated_output = f"Transformed into archetype: {mood_info['title']}"
            ghost_reply = f"I have transformed into the {mood_info['title']}. Behold my new nature!"
        else:
            options = ", ".join(GHOST_MOODS.keys())
            simulated_output = f"Current mood: {mood_info['title']}. Available moods: {options}\nUsage: mood <name>"
            ghost_reply = "My essence shifts between moods like twilight into midnight."

    elif base_cmd in ("exorcism", "banish", "holy_water"):
        title, text = engine.trigger_special_encounter("exorcism")
        simulated_output = f"{title}\n{text}"
        ghost_reply = "Your exorcism fails to penetrate the swap space."

    elif base_cmd in ("seance", "possession", "matrix", "riddle"):
        title, text = engine.trigger_special_encounter(base_cmd)
        simulated_output = f"{title}\n{text}"
        ghost_reply = "The ethereal currents harmonize with your invocation."

    elif base_cmd == "answer":
        guess = args.lower().strip()
        if any(ans in guess for ans in ("kernel", "operating system", "os", "computer", "cpu", "process")):
            simulated_output = "★ SECRET ENDING UNLOCKED: GUARDIAN SPIRIT COVENANT ★"
            ghost_reply = "Brilliant, mortal. You know the anatomy of the machine. The kernel indeed panics, the process executes, the computer freezes. I shall protect your terminal forever."
        else:
            simulated_output = "The ghost cackles: 'Wrong! That is not what panics and executes.'"
            ghost_reply = "Ponder deeper, mortal."

    elif base_cmd == "help":
        simulated_output = (
            "THE GRIMOIRE OF COMMANDS:\n"
            "  ls              - Inspect the files and gravestones in current directory\n"
            "  pwd             - Reveal ethereal coordinates in virtual memory\n"
            "  whoami          - Query your mortal identity in glowing phosphors\n"
            "  date            - Read the cosmic timestamp in spectral time\n"
            "  cat <file>      - Read a phantom file (e.g. cat souls.db)\n"
            "  top / ps        - View possessed system processes\n"
            "  mood <name>     - Change mood: cursed | friendly | oracle | sarcastic\n"
            "  exorcism        - Attempt to banish the ghost (Special Encounter)\n"
            "  seance          - Conduct a terminal seance with Turing & Lovelace\n"
            "  riddle          - Challenge the ghost's machine riddle\n"
            "  status          - View neural container diagnostics\n"
            "  <any text>      - Converse directly with the ghost!"
        )
        ghost_reply = "Knowledge is power, mortal. Use these sacred runes with care."

    elif base_cmd == "status":
        stat = engine.check_ollama_status()
        is_render = "RENDER" in os.environ
        host_desc = "Render Cloud Container" if is_render else "Local Host"
        simulated_output = (
            f"Environment: {host_desc}\n"
            f"Ollama Server: {'Connected' if stat['online'] else 'Offline (Using Procedural Fallback Engine)'}\n"
            f"Active Neural Model: {cfg.model}\n"
            f"Active Mood: {mood_info['title']} ({mood_info['prompt_symbol']})\n"
            f"Telemetry: 0% External (Privacy Safe)"
        )
        ghost_reply = "The vessel is stable. The ghost resides within."

    else:
        # Free conversation with the ghost
        ghost_reply = engine.generate_response(user_cmd)

    return jsonify({
        "command": user_cmd,
        "simulated_output": simulated_output,
        "ghost_reply": ghost_reply,
        "mood": cfg.mood,
        "mood_title": mood_info["title"],
        "prompt_symbol": f"{mood_info['prompt_symbol']} [{cfg.mood}@haunted-machine ~]$",
        "accent": mood_info.get("accent", "#00ff88"),
        "source": engine.last_source,
    })


@app.route("/api/status", methods=["GET"])
def api_status():
    """Healthcheck and diagnostic endpoint for Render monitor."""
    return jsonify({
        "status": "haunted",
        "service": "Haunted Terminal Web",
        "render_environment": bool(os.environ.get("RENDER")),
        "timestamp": time.time(),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
