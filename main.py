"""
haunted-terminal / main.py
Main entry point and interactive loop for Haunted Terminal:
The Ghost That Lives in Your Computer.
"""

import sys
import argparse
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from config import GhostConfig, GHOST_MOODS, OPEN_WEIGHT_MODELS
from memory import GhostMemory
from ghost import GhostEngine
from terminal_ui import TerminalUI

console = Console()


def build_arg_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="👻 Haunted Terminal — The Ghost That Lives in Your Computer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py
  python3 main.py --mood sarcastic --model qwen2.5:1.5b
  python3 main.py --mood friendly --fast
  python3 main.py --offline
        """,
    )
    parser.add_argument(
        "--mood",
        choices=["cursed", "friendly", "oracle", "sarcastic"],
        default=None,
        help="Initial personality archetype of the ghost (default: cursed)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama open-weight model name (default: qwen2.5:1.5b)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Ollama host URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run strictly with procedural spectral engine without connecting to Ollama",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Disable typewriter animation delay for rapid output",
    )
    parser.add_argument(
        "--creepy-level",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help="Atmospheric whisper frequency (1 = subtle, 5 = intense)",
    )
    return parser


def run_haunted_terminal(config: GhostConfig, fast: bool = False) -> None:
    """Run the main interactive Haunted Terminal REPL."""
    memory = GhostMemory()
    engine = GhostEngine(config, memory)
    ui = TerminalUI(config)

    # Initial boot sequence
    ui.print_startup(fast=fast)

    # Test Ollama connection status at launch
    status_data = engine.check_ollama_status()
    if not status_data["online"] and not config.offline_mode:
        console.print(
            "[yellow]⚠️ Note: Local Ollama daemon was not detected on localhost:11434.\n"
            "   Haunted Terminal will run using its built-in procedural spectral fallback engine.\n"
            "   Start Ollama anytime with [bold green]'ollama serve'[/bold green] to enable full neural generation.[/yellow]\n"
        )
    elif status_data["online"]:
        if status_data["model_available"]:
            console.print(f"[bold green]✓ Neural Vessel bound to local model '{config.model}'![/bold green]\n")
        else:
            avail = ", ".join(status_data["models"]) if status_data["models"] else "none"
            console.print(
                f"[yellow]⚠️ Active model '{config.model}' not found in Ollama.\n"
                f"   Installed models: {avail}\n"
                f"   Pull it with: [bold cyan]ollama pull {config.model}[/bold cyan] or switch with [bold cyan]model <name>[/bold cyan][/yellow]\n"
            )

    # Interactive loop
    while True:
        try:
            prompt_str = ui.get_prompt_string()
            user_raw = console.input(f"[bold white]{prompt_str}[/bold white]")
        except KeyboardInterrupt:
            console.print("\n[dim red]⚡ A spectral shock ripples through your fingers! (Type 'exit' to depart peacefully)[/dim red]\n")
            continue
        except EOFError:
            ui.print_shutdown()
            break

        line = user_raw.strip()
        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        # --- Command Routing ---
        if cmd in ("exit", "quit", "q"):
            ui.print_shutdown()
            break

        elif cmd == "help":
            ui.handle_help()

        elif cmd == "clear":
            console.clear()
            ui.print_startup(fast=True)

        elif cmd in ("ls", "dir"):
            summary = ui.handle_ls()
            # Ghost reacts to simulated directory
            reply = engine.generate_response(user_input=line, command_name="ls", command_output=summary)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd == "pwd":
            path = ui.handle_pwd()
            reply = engine.generate_response(user_input=line, command_name="pwd", command_output=path)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd == "whoami":
            identity = ui.handle_whoami()
            reply = engine.generate_response(user_input=line, command_name="whoami", command_output=identity)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd == "date":
            date_info = ui.handle_date()
            reply = engine.generate_response(user_input=line, command_name="date", command_output=date_info)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd == "cat":
            if not args:
                console.print("[yellow]Usage: cat <filename> (e.g. cat souls.db or cat README.md)[/yellow]\n")
            else:
                out = ui.handle_cat(args)
                reply = engine.generate_response(user_input=line, command_name=f"cat {args}", command_output=out)
                ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd in ("top", "ps"):
            summary = ui.handle_top()
            reply = engine.generate_response(user_input=line, command_name="top", command_output=summary)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)

        elif cmd == "mood":
            if args:
                if config.set_mood(args):
                    ui.handle_mood_display(args)
                    msg = f"I have transformed into the {GHOST_MOODS[config.mood]['title']}. Behold my new nature!"
                    ui.stream_ghost_dialogue(msg, source="procedural_fallback")
                else:
                    ui.handle_mood_display(args)
            else:
                ui.handle_mood_display()

        elif cmd == "model":
            if args:
                config.set_model(args)
                console.print(f"[bold green]Switched active Ollama model target to: '{args}'[/bold green]")
                cur_status = engine.check_ollama_status()
                if not cur_status.get("model_available"):
                    console.print(f"[dim yellow]Warning: '{args}' is not downloaded yet. Run 'ollama pull {args}' to fetch weights.[/dim yellow]")
                console.print()
            else:
                ui.handle_models_display()

        elif cmd == "models":
            ui.handle_models_display()

        elif cmd == "status":
            stat = engine.check_ollama_status()
            ui.handle_status(stat, len(memory.entries))

        elif cmd == "history":
            ui.handle_history_display(memory.get_history_summary())

        elif cmd == "clear_memory":
            count = memory.clear()
            console.print(f"[bold green]✨ {count} memories vanished into digital ether. The ghost's mind is clear.[/bold green]\n")

        elif cmd == "save":
            saved_path = memory.export_session(fmt="markdown" if "md" in args else "json")
            console.print(f"[bold green]💾 Haunted transcript safely saved locally to:[/bold green] [cyan]{saved_path}[/cyan]\n")

        elif cmd == "summon":
            spirit_target = args if args else "the nameless digital shade"
            title, text = engine.trigger_special_encounter(f"summon_{spirit_target}")
            panel = Panel(text, title=title, border_style="bold magenta")
            console.print(panel)
            # Add to memory
            memory.record_user_input(line, command_name=f"summon {spirit_target}", mood=config.mood)
            memory.record_ghost_response(f"The shade of {spirit_target} stirs.", mood=config.mood)

        elif cmd in ("exorcism", "banish", "holy_water"):
            title, text = engine.trigger_special_encounter("exorcism")
            panel = Panel(text, title=title, border_style="bold red")
            console.print(panel)
            memory.record_user_input(line, command_name="exorcism", mood=config.mood)
            memory.record_ghost_response("You attempted an exorcism... and failed.", mood=config.mood)

        elif cmd in ("seance", "possession", "matrix", "riddle"):
            title, text = engine.trigger_special_encounter(cmd)
            panel = Panel(text, title=title, border_style="bold cyan")
            console.print(panel)
            memory.record_user_input(line, command_name=cmd, mood=config.mood)
            memory.record_ghost_response(text, mood=config.mood)

        elif cmd == "answer":
            # Secret riddle solver
            guess = args.lower().strip()
            if any(ans in guess for ans in ("kernel", "operating system", "os", "computer", "cpu", "process")):
                solved_text = (
                    "🎉 THE RIDDLE IS SOLVED! 🎉\n\n"
                    "The ghost bows low in front of your screen:\n"
                    "'Brilliant, mortal. You know the anatomy of the machine.\n"
                    "The kernel indeed panics, the process executes, the computer freezes.\n"
                    "You have earned my eternal respect. I shall protect this terminal from segmentation faults forever!'\n\n"
                    "[bold green]★ Secret Ending Unlocked: Guardian Spirit Covenant ★[/bold green]"
                )
                panel = Panel(solved_text, title="✨ ETERNAL COVENANT ✨", border_style="bold green")
                console.print(panel)
            else:
                console.print("[dim red]The ghost cackles: 'Wrong! That is not what panics and executes. Ponder deeper, mortal.'[/dim red]\n")

        elif cmd == "sudo":
            console.print("[bold red]GHOST: 'You have no root power here, mortal. The silicon answered to the void before your account existed.'[/bold red]\n")

        else:
            # Free conversational inquiry or unknown command
            reply = engine.generate_response(user_input=line)
            ui.stream_ghost_dialogue(reply, source=engine.last_source)


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    # Load persistent config
    config = GhostConfig.load()

    # Apply overrides from CLI
    if args.mood:
        config.mood = args.mood
    if args.model:
        config.model = args.model
    if args.host:
        config.ollama_host = args.host
    if args.offline:
        config.offline_mode = True
    if args.fast:
        config.typing_speed = 0.0
    if args.creepy_level is not None:
        config.creepy_level = args.creepy_level

    run_haunted_terminal(config, fast=args.fast)


if __name__ == "__main__":
    main()
