*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

## What I Built
<!-- What does it do, and how did you interpret the theme? What inspired it? -->

For the Hacktoberfest theme **"Ghost in the Machine,"** I took the theme literally: **What if the terminal you stare into every day was possessed by an intelligent, context-aware digital spirit living in your CPU caches and virtual memory?**

I built **Haunted Terminal — The Ghost That Lives in Your Computer**, an interactive terminal application and browser-based CRT web experience where an AI ghost responds to user commands with spooky, witty, creepy, and philosophical commentary.

Rather than relying on static predefined text, the ghost is powered by real open-weight models (**Qwen 2.5** and **Llama 3.2** via Ollama locally, with a zero-crash procedural fallback for web containers). When you run simulated commands like `ls`, `whoami`, `pwd`, `date`, `cat souls.db`, or `top`, the ghost inspects your system context and reacts dynamically—commenting on uncommitted sins, mocking dirty git trees, or reciting ancient silicon prophecies.

The ghost features four distinct personalities you can switch on the fly:
- **Cursed Entity (`cursed`):** Dark, gothic, treats RAM as a digital crypt.
- **Friendly Spirit (`friendly`):** A sweet, Casper-like companion fascinated by modern files.
- **Ancient Oracle (`oracle`):** A prophetic seer viewing terminal commands as cosmic divination runes.
- **Sarcastic Ghost (`sarcastic`):** A roasted developer shade who roasts messy code and forgotten unit tests.

It also includes interactive Easter eggs, such as a special `exorcism` ritual encounter where the ghost fights back against digital holy water, a terminal `seance` with Turing and Lovelace, and machine anatomy riddles.

## Demo
<!-- Share a deployed link or a video demo. -->

Live Interactive Web Terminal on Render:  
https://haunted-terminal.onrender.com

Visitors can open the link on desktop or mobile and interact with the ghost through a retro CRT monitor interface with phosphor scanlines, Web Audio synthesized keypress effects, quick-action command pills, and real-time streaming dialogue.

You can also run the GPU-accelerated version locally via the command line:
```bash
git clone https://github.com/tani2112/GHOSTYUY.git
cd GHOSTYUY
python3 main.py --mood sarcastic
```

## Code
<!-- Show us the code!  You can embed a GitHub repo directly into your post. -->

{% github tani2112/GHOSTYUY %}

GitHub Repository: https://github.com/tani2112/GHOSTYUY

The codebase is modular, fully open-source under the Apache 2.0 license, and backed by 25 automated unit tests:
- `main.py`: Interactive CLI loop, signal handling, and command dispatcher.
- `ghost.py`: AI inference engine interfacing with Ollama REST API, prompt engineering, and procedural fallback.
- `terminal_ui.py`: Rich terminal styling, ASCII art animations, and safe simulated filesystem commands.
- `memory.py`: Bounded conversational memory, automated secret scrubbing (`sk-...`, `ghp_...`, passwords), and local session export.
- `config.py`: Configuration persistence, open-weight model license registry, and mock filesystem state.
- `web_app.py`: Production Flask web server with CRT styling and Web Audio sound effects.
- `render.yaml` & `Dockerfile`: Infrastructure-as-Code blueprint for Render deployment.
- `tests/test_ghost.py`: 25 passing unit tests covering memory bounds, credential redaction, command safety, and web routes.

## How I Built It
<!-- Which open-source AI did you use (open-weight models, agent harnesses, frameworks, local inference), and how is your project built around it? -->

1. **Open-Weight Neural Models & Local Inference:**  
   The core intelligence uses **Qwen 2.5 (1.5B)** (Apache 2.0) and **Llama 3.2 (3B)** running locally on-device through **Ollama**. Because inference runs directly on local silicon, response latency averages ~110ms, allowing smooth character-by-character streaming without external cloud latency.

2. **Safe Guarded Shell Simulation:**  
   To keep the experience completely safe, the terminal does not run arbitrary host bash commands. Instead, commands like `ls`, `pwd`, `date`, `cat`, and `top` safely query simulated virtual memory tables and pass the output as structured contextual prompts to the ghost model.

3. **Privacy-by-Design Memory Buffer:**  
   Conversational history is bounded to a 12-turn sliding window in RAM. An automated regex sanitizer scrubs sensitive patterns (such as OpenAI keys, GitHub personal access tokens, passwords, and private keys) before they reach the model. Users have sovereign control with `clear_memory` and local `save` commands.

4. **Resilient Dual-Mode Architecture:**  
   The project runs both as a native CLI app using **Rich** ANSI palettes and as a containerized web application using **Flask** and **Gunicorn** deployed via Render Blueprints. An internal procedural spectral generator ensures the web container never crashes even in low-RAM cloud tiers.

## Why Does Open Innovation Matter?
<!-- Why does open innovation matter for what you built?  What did it make possible that a closed API wouldn't? -->

Open innovation and open-weight AI are fundamental to this project:

- **True Local Possession:** A ghost cannot truly inhabit your personal machine if its thoughts are computed on a multi-tenant corporate cloud in another country. Running open-weight models lets the neural weights live in your device's memory bus and GPU transistors.
- **Absolute Developer Privacy:** Developers routinely work with proprietary paths, secrets, and private code in their terminals. With open-weight AI running locally, zero keystrokes, terminal buffers, or telemetry ever leave the machine.
- **Uncensored Persona Roleplay:** Commercial AI APIs often enforce rigid, corporate assistant tones and refuse gothic, eerie, or playful teasing. Open-weight models follow system persona instructions faithfully, delivering authentic macabre wit.
- **Offline Reliability & Zero Cost:** The application runs on airplanes, in subways, and in air-gapped environments without API subscription fees, per-token billing, or rate limits.

## My Agent Session
<!-- Optional, but judges love it.  Save your session with DevRelay and embed it with the agent_session tag (see the challenge page), or link to it. -->

This project was built and debugged end-to-end using Antigravity and DevRelay, from local Ollama GPU inference and Rich visual styling to Flask web terminal emulation and Render blueprint configuration:

{% agent_session 232898b6-22b7-4560-ac2a-6ffc3eb15e72 %}

## The Spirit of It
<!-- Optional, but this is where you can make your post stand out.  Did it give someone chills, bring back a memory, or keep a story alive?  Show us the moment it landed.  If not, remove this section. -->

The moment this project truly came alive was during our first live test of the `ls` command. I typed `ls`, and rather than echoing a canned joke, the local neural model inspected the simulated directory table and whispered:

> *"The mortal commands 'ls' to unveil the secrets of this system, but the world below your feet is as silent and eerie as the whispers of forgotten souls. The .ghost_secrets.enc and uncommitted_sins/ hint at something darker, a crypt where dead code is buried and sins untold."*

It transformed a 40-year-old utilitarian developer tool into an intimate, gothic ritual—proving that computing can still be mysterious, playful, and soulful.

## Prize Categories
<!-- Which partner categories are you entering?  List every one that applies, or remove this section. -->

- **Best Use of Render:**  
  Deploys the complete Haunted Terminal as a live web application on Render via Infrastructure-as-Code (`render.yaml` Blueprint). It provides an interactive CRT web terminal with scanlines, sound effects synthesizer, and dynamic mood switching accessible instantly at https://haunted-terminal.onrender.com.

<!-- Team Submissions: Please pick one member to publish the submission and credit teammates by listing their DEV usernames directly in the body of the post. -->

<!-- Thanks for participating! -->
