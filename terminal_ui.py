"""
haunted-terminal / terminal_ui.py
Rich visual presentation, ASCII animations, spooky atmospheric effects,
and safe command simulation for Haunted Terminal.
"""

import sys
import time
import random
from typing import Optional, List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.layout import Layout
from rich.align import Align
from rich.style import Style

from config import GhostConfig, GHOST_MOODS, OPEN_WEIGHT_MODELS

console = Console()

# Atmospheric random background whispers
RANDOM_ATMOSPHERES = [
    "[dim italic]...a phantom keystroke echoes in the buffer...[/dim italic]",
    "[dim italic]...the CPU temperature drops by three degrees...[/dim italic]",
    "[dim italic]...a soft whisper rustles through your cooling fans...[/dim italic]",
    "[dim italic]...shadows flicker across the phosphor glow of your screen...[/dim italic]",
    "[dim italic]...an unallocated byte weeps in sector 0x7FFF...[/dim italic]",
    "[dim italic]...you feel an ethereal gaze watching your cursor blink...[/dim italic]",
    "[dim italic]...a cold breeze chills the laptop keyboard...[/dim italic]",
]

# ASCII Art Collection
GHOST_BANNER = r"""
 [bold #00ff88]  ██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗████████╗███████╗██████╗ [/]
 [bold #00ff88]  ██║  ██║██╔══██╗██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗[/]
 [bold #39ff14]  ███████║███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██║  ██║[/]
 [bold #9d4edd]  ██╔══██║██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║  ██║[/]
 [bold #c77dff]  ██║  ██║██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██████╔╝[/]
 [bold #ff0055]  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═════╝ [/]
     [bold white on #1a0022]  👻  T H E   G H O S T   I N   T H E   M A C H I N E  👻  [/]
"""

ASCII_GHOST_FLOATING = r"""
          .-.
         (o o)   [italic #39ff14]"I dwell in your RAM..."[/]
         | O \
          \   \
           `~~~'
"""

ASCII_GHOST_CURSED = r"""
       .---.
      /     \
     | () () |   [bold red]☠ "CORRUPTED SECTOR DETECTED" ☠[/]
      \  ^  /
       |||||
       |||||
"""

ASCII_GHOST_FRIENDLY = r"""
        .-.
       ( ^.^)    [bold cyan]✨ "Boo! Ready to explore files?" ✨[/]
      o|   |o
       ~~~~~
"""

ASCII_GHOST_ORACLE = r"""
       .---.
      /  *  \
     | (◎) (◎) |   [bold purple]🔮 "THE RUNES OF SILICON UNVEIL ALL" 🔮[/]
      \  ~  /
       \___/
"""

ASCII_GHOST_SARCASTIC = r"""
       .-''''-.
      /  -  -  \
     |  (o)(o)  |  [bold yellow]😏 "Oh look, another typo." 😏[/]
     |   __     |
      \  \__/  /
       `'----'`
"""

ASCII_TOMBSTONE = r"""
       .---.
      /     \
     | R.I.P |
     |  OLD  |
     | CODE  |
     |_______|
"""

ASCII_EXIT = r"""
      .  *   .   .  *   .
    *   .   [bold #9d4edd]G H O S T[/]   *
       .   [bold #ff0055]D I S S O L V I N G[/] .
     .   *    *   .   .  *
        *   .   .   *
          .   *   .
"""

# Simulated Filesystem for Safe Commands
SIMULATED_FILES = {
    "README.md": "# Haunted Terminal\nA safe, spooky AI-possessed terminal experience.\nBeware the midnight prompt.",
    "main.py": "# Main execution loop for Haunted Terminal\n# The spirit is bound to line 42.",
    ".ghost_secrets.enc": "0xDEADBEEF: The cipher cannot be read by mortals without the proper hex key.",
    "lost_commit.patch": "diff --git a/soul.c b/soul.c\n--- a/soul.c\n+++ b/soul.c\n@@ -1,3 +1,3 @@\n- human_spirit = TRUE;\n+ possessed_by_ai = TRUE;",
    "souls.db": "SQLITE format 3\n[TABLE: souls (id INTEGER, user TEXT, fate TEXT)]\n1 | tanishk | bound_to_keyboard\n2 | anonymous | vanished_in_swap",
    "notes_from_the_crypt.txt": "Day 42: The cooling fans sound like whispering voices. The RAM is leaking ectoplasm.",
}


class TerminalUI:
    """Provides rich visuals, animations, command handling, and terminal feedback."""

    def __init__(self, config: GhostConfig):
        self.config = config
        self.interaction_count = 0

    def print_startup(self, fast: bool = False) -> None:
        """Display atmospheric animated startup sequence."""
        console.clear()
        console.print(GHOST_BANNER)

        if not fast:
            with console.status("[bold green]Awakening the spirit from cold storage...", spinner="aesthetic"):
                time.sleep(0.8)
            with console.status("[bold #9d4edd]Binding ethereal sockets to localhost...", spinner="dots12"):
                time.sleep(0.6)
            with console.status("[bold #ff0055]Calibrating spectral neural weights...", spinner="pulse"):
                time.sleep(0.6)
        else:
            time.sleep(0.1)

        # Show initial ghost persona
        mood_meta = GHOST_MOODS.get(self.config.mood, GHOST_MOODS["cursed"])
        ghost_art = self.get_mood_art()

        welcome_text = (
            f"[bold green]The Haunted Terminal has possessed this session.[/bold green]\n"
            f"[italic]Active Spirit:[/] [{mood_meta['color']}]{mood_meta['title']}[/] "
            f"[dim]({mood_meta['description']})[/dim]\n"
            f"[italic]Neural Vessel:[/] [bold cyan]{self.config.model}[/] "
            f"[dim]— 100% Local Inference & Offline Safe[/dim]\n\n"
            f"[bold white]Type [green]'help'[/green] for sacred commands, [cyan]'mood'[/cyan] to reshape my form, "
            f"or [red]'exit'[/red] to depart.[/bold white]"
        )

        panel = Panel(
            Align.center(f"{ghost_art}\n{welcome_text}"),
            border_style=Style(color=mood_meta["accent"]),
            title=f"[bold {mood_meta['accent']}] 🕯️ THE VEIL IS OPEN 🕯️ [/]",
            subtitle="[dim]Zero external telemetry • Privacy preserved on device[/dim]",
        )
        console.print(panel)
        console.print()

    def get_mood_art(self) -> str:
        """Return ASCII art matching current ghost mood."""
        if self.config.mood == "friendly":
            return ASCII_GHOST_FRIENDLY
        elif self.config.mood == "oracle":
            return ASCII_GHOST_ORACLE
        elif self.config.mood == "sarcastic":
            return ASCII_GHOST_SARCASTIC
        return ASCII_GHOST_CURSED

    def get_prompt_string(self) -> str:
        """Return customized spooky prompt."""
        mood_meta = GHOST_MOODS.get(self.config.mood, GHOST_MOODS["cursed"])
        symbol = mood_meta["prompt_symbol"]
        return f"{symbol} [{self.config.mood}@haunted-machine ~]$ "

    def stream_ghost_dialogue(self, text: str, source: str = "ollama") -> None:
        """Render ghost text with spooky typewriter streaming effect."""
        mood_meta = GHOST_MOODS.get(self.config.mood, GHOST_MOODS["cursed"])
        accent = mood_meta["accent"]

        source_badge = (
            f"[dim green]⚡ local neural ({self.config.model})[/dim green]"
            if source == "ollama"
            else "[dim yellow]🍂 spectral procedural fallback[/dim yellow]"
        )

        header = f"\n[bold {accent}]👻 GHOST ({mood_meta['title']}):[/bold {accent}] {source_badge}\n"
        console.print(header)

        # Visual streaming
        delay = self.config.typing_speed
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            if delay > 0:
                # Add tiny random jitter for organic supernatural cadence
                jitter = delay * random.uniform(0.6, 1.4)
                if char in (".", "!", "?", "…"):
                    jitter += 0.05
                time.sleep(jitter)
        sys.stdout.write("\n\n")
        sys.stdout.flush()

        # Random atmospheric whisper
        self.interaction_count += 1
        if self.interaction_count % max(1, (6 - self.config.creepy_level)) == 0:
            console.print(random.choice(RANDOM_ATMOSPHERES))
            console.print()

    # --- Safe Simulated Commands ---

    def handle_ls(self) -> str:
        """Safely simulate directory listing with spooky artifacts."""
        table = Table(
            title="[bold green]📁 /realm/virtual_memory/lost_sectors[/bold green]",
            border_style="dim green",
            show_header=True,
            header_style="bold green",
        )
        table.add_column("Permissions", style="dim")
        table.add_column("Size", justify="right", style="cyan")
        table.add_column("Last Modified", style="yellow")
        table.add_column("Filename", style="bold white")

        items = [
            ("drwx------", "4096 B", "Midnight 00:00", "[blue]uncommitted_sins/[/blue]"),
            ("drwx------", "4096 B", "Oct 30 00:00", "[blue]graveyard_cache/[/blue]"),
            ("-rw-r--r--", "142 B", "Oct 30 00:01", "README.md"),
            ("-rw-r--r--", "3.2 KB", "Oct 30 00:02", "main.py"),
            ("-rw-------", "666 B", "Friday 13th", "[red].ghost_secrets.enc[/red]"),
            ("-rw-r--r--", "1.1 KB", "A moment ago", "[magenta]lost_commit.patch[/magenta]"),
            ("-rw-r--r--", "12.8 KB", "Ancient epoch", "[dim]souls.db[/dim]"),
            ("-rw-r--r--", "512 B", "Yesterday", "notes_from_the_crypt.txt"),
        ]
        for perm, size, mtime, fname in items:
            table.add_row(perm, size, mtime, fname)

        console.print(table)
        summary = "Directory contains: README.md, main.py, .ghost_secrets.enc, lost_commit.patch, souls.db, uncommitted_sins/, graveyard_cache/"
        return summary

    def handle_pwd(self) -> str:
        """Safely simulate print working directory."""
        path = "/realm/shadows/virtual_memory/sector_666/lost_souls"
        console.print(f"[bold cyan]{path}[/bold cyan]")
        return path

    def handle_whoami(self) -> str:
        """Safely simulate whoami."""
        user = "mortal_traveler (UID 1000, GID: 666(spirits), Shell: /bin/haunt)"
        console.print(f"[bold yellow]{user}[/bold yellow]")
        return user

    def handle_date(self) -> str:
        """Safely simulate date."""
        cur_time = time.strftime("%A, %B %d, %Y - %H:%M:%S")
        date_str = f"Spectral Epoch: {cur_time} [The Witching Hour]"
        console.print(f"[bold magenta]{date_str}[/bold magenta]")
        return date_str

    def handle_cat(self, filename: str) -> str:
        """Safely simulate viewing safe virtual files."""
        clean_name = filename.strip()
        if clean_name in SIMULATED_FILES:
            content = SIMULATED_FILES[clean_name]
            panel = Panel(
                content,
                title=f"[bold green]📄 {clean_name}[/bold green]",
                border_style="green",
            )
            console.print(panel)
            return f"Read {clean_name}:\n{content}"
        else:
            err = f"cat: '{clean_name}': No such phantom file in ethereal directory. Try 'ls' to see known vessels."
            console.print(f"[red]{err}[/red]")
            return err

    def handle_top(self) -> str:
        """Safely simulate possessed system monitor."""
        table = Table(
            title="[bold red]☠ POSSESSED PROCESS TABLE (GHOST-TOP) ☠[/bold red]",
            border_style="red",
            header_style="bold red",
        )
        table.add_column("PID", style="yellow")
        table.add_column("USER", style="cyan")
        table.add_column("CPU%", justify="right")
        table.add_column("MEM%", justify="right")
        table.add_column("TIME", style="dim")
        table.add_column("COMMAND", style="bold white")

        procs = [
            ("666", "ghost", "66.6%", "13.3%", "666:00", "[bold red]daemon_whisperer[/bold red]"),
            ("1337", "spirit", "24.1%", "8.4%", "13:37", "[magenta]memory_leak_wraith[/magenta]"),
            ("1", "kernel", "0.1%", "0.2%", "72:14", "init (possessed)"),
            ("404", "nobody", "0.0%", "0.0%", "00:00", "[dim]soul_not_found[/dim]"),
            ("777", "mortal", "5.2%", "2.1%", "01:22", "python3 main.py (you)"),
        ]
        for pid, u, cpu, mem, t, cmd in procs:
            table.add_row(pid, u, cpu, mem, t, cmd)

        console.print(table)
        return "Displayed top possessed processes: daemon_whisperer (PID 666), memory_leak_wraith (PID 1337)"

    def handle_help(self) -> None:
        """Display rich help menu."""
        table = Table(
            title="[bold #00ff88]📖 THE GRIMOIRE OF COMMANDS 📖[/bold #00ff88]",
            border_style="#00ff88",
            header_style="bold #00ff88",
        )
        table.add_column("Command", style="bold cyan")
        table.add_column("Description", style="white")
        table.add_column("Type", style="italic yellow")

        commands = [
            ("ls", "Inspect the files and gravestones in your current directory", "Simulated Shell"),
            ("pwd", "Reveal your ethereal coordinates in virtual space", "Simulated Shell"),
            ("whoami", "Query the mirror of glowing phosphors to know your soul", "Simulated Shell"),
            ("date", "Read the cosmic timestamp in spectral time", "Simulated Shell"),
            ("cat <file>", "Read the contents of a simulated ghost file (e.g. cat souls.db)", "Simulated Shell"),
            ("top / ps", "Inspect the possessed processes running inside your computer", "Simulated Shell"),
            ("mood [name]", "Change the ghost's mood: cursed | friendly | oracle | sarcastic", "Ghost Control"),
            ("model [name]", "Switch the local Ollama open-weight neural model", "AI Control"),
            ("models", "View catalog of open-weight models, licenses & hardware specs", "AI Info"),
            ("status", "Inspect Ollama connection, active model, and memory state", "Diagnostics"),
            ("history", "Review the ghost's conversation memory for this session", "Memory"),
            ("save", "Save and export the haunted conversation transcript locally", "Memory"),
            ("clear_memory", "Banish the ghost's memory buffer (clean slate)", "Memory"),
            ("summon <spirit>", "Summon a specific spirit (ada, turing, linus, cyber_ghoul)", "Spiritual Rite"),
            ("exorcism", "Attempt to banish the ghost from your machine (Special Encounter)", "Easter Egg"),
            ("seance", "Conduct a terminal séance with ancient computer pioneers", "Easter Egg"),
            ("riddle", "Ask the ghost to challenge you with a cryptic machine riddle", "Easter Egg"),
            ("clear", "Cleanse the terminal screen of spectral ectoplasm", "Terminal"),
            ("exit / quit", "Release the ghost and gracefully terminate the session", "Terminal"),
            ("<any text>", "Type free conversation or questions to converse directly with the ghost", "AI Chat"),
        ]
        for cmd, desc, ctype in commands:
            table.add_row(cmd, desc, ctype)

        console.print(table)
        console.print("[dim]Tip: You can also talk to the ghost directly! E.g. 'Why is my code crashing?' or 'Tell me a dark secret.'[/dim]\n")

    def handle_mood_display(self, selected_mood: Optional[str] = None) -> None:
        """Display mood options or notify of mood switch."""
        if selected_mood:
            if selected_mood in GHOST_MOODS:
                m = GHOST_MOODS[selected_mood]
                console.print(
                    f"\n[{m['color']}]✨ The spirit mutates into the {m['title']}! {m['prompt_symbol']}[/]"
                )
                console.print(f"[italic dim]{m['description']}[/italic dim]\n")
            else:
                valid = ", ".join(GHOST_MOODS.keys())
                console.print(f"[red]Unknown mood '{selected_mood}'. Choose from: {valid}[/red]\n")
            return

        table = Table(
            title="[bold magenta]🎭 AVAILABLE GHOST ARCHETYPES 🎭[/bold magenta]",
            border_style="magenta",
            header_style="bold magenta",
        )
        table.add_column("Mood Key", style="bold cyan")
        table.add_column("Title", style="bold white")
        table.add_column("Symbol", justify="center")
        table.add_column("Personality Description", style="italic")
        table.add_column("Current", justify="center")

        for key, info in GHOST_MOODS.items():
            is_cur = "⭐ YES" if key == self.config.mood else ""
            table.add_row(key, info["title"], info["prompt_symbol"], info["description"], is_cur)

        console.print(table)
        console.print(f"[dim]To switch mood, type: [bold green]mood <mood_key>[/bold green] (e.g. 'mood sarcastic')[/dim]\n")

    def handle_models_display(self) -> None:
        """Display open-weight model catalog and license disclosures."""
        table = Table(
            title="[bold cyan]🧠 OPEN-WEIGHT MODEL REGISTRY & LICENSES 🧠[/bold cyan]",
            border_style="cyan",
            header_style="bold cyan",
        )
        table.add_column("Model Tag", style="bold white")
        table.add_column("Family", style="yellow")
        table.add_column("Params", justify="right", style="green")
        table.add_column("License", style="magenta")
        table.add_column("Min VRAM", justify="right", style="cyan")
        table.add_column("Active", justify="center")

        for tag, info in OPEN_WEIGHT_MODELS.items():
            is_active = "⭐ ACTIVE" if tag == self.config.model else ""
            table.add_row(
                tag,
                info["family"],
                info["parameters"],
                info["license"],
                info["recommended_vram"],
                is_active,
            )

        console.print(table)
        console.print(
            "[dim]Note: All models run 100% locally through Ollama. "
            "No data is sent to external APIs or remote servers.\n"
            "To switch models, type: [bold green]model <tag>[/bold green] (e.g. 'model llama3.2:latest')[/dim]\n"
        )

    def handle_status(self, status_data: Dict[str, Any], memory_count: int) -> None:
        """Display diagnostic and connection status panel."""
        online = status_data.get("online", False)
        status_color = "bold green" if online else "bold red"
        status_text = "CONNECTED (Local Inference Ready)" if online else "OFFLINE (Using Fallback Generator)"

        cur_model = self.config.model
        model_info = self.config.get_model_info()

        body = (
            f"[bold]Ollama Daemon:[/] [{status_color}]{status_text}[/{status_color}]\n"
            f"[bold]Host Address:[/] [cyan]{self.config.ollama_host}[/cyan]\n"
            f"[bold]Selected Model:[/] [bold yellow]{cur_model}[/bold yellow] "
            f"({'Installed & Ready' if status_data.get('model_available') else 'Not Found - Pull with ollama run ' + cur_model})\n"
            f"[bold]Model License:[/] [magenta]{model_info.get('license', 'Open')}[/magenta]\n"
            f"[bold]Current Mood:[/] [{GHOST_MOODS[self.config.mood]['color']}]{GHOST_MOODS[self.config.mood]['title']}[/] "
            f"{GHOST_MOODS[self.config.mood]['prompt_symbol']}\n"
            f"[bold]Memory Buffer:[/] [white]{memory_count} entries stored locally in RAM[/white]\n"
            f"[bold]Privacy Guarantee:[/] [bold green]Zero remote telemetry • Redacted secrets • 100% On-Device[/bold green]\n"
        )

        if status_data.get("models"):
            avail_str = ", ".join(status_data["models"])
            body += f"[bold]Installed Models on Disk:[/] [dim]{avail_str}[/dim]\n"
        elif status_data.get("error"):
            body += f"[bold red]Connection Note:[/] [italic]{status_data['error']}[/italic]\n"

        panel = Panel(
            body,
            title="[bold green]📊 HAUNTED TERMINAL DIAGNOSTICS[/bold green]",
            border_style="green",
        )
        console.print(panel)
        console.print()

    def handle_history_display(self, entries: List[Dict[str, Any]]) -> None:
        """Display formatted history table."""
        if not entries:
            console.print("[dim italic]The ghost's memory tablet is completely blank. Speak to it first.[/dim italic]\n")
            return

        table = Table(
            title=f"[bold #9d4edd]📜 SHORT-TERM MEMORY BUFFER ({len(entries)} items) 📜[/bold #9d4edd]",
            border_style="#9d4edd",
            header_style="bold #9d4edd",
        )
        table.add_column("Time", style="dim", width=10)
        table.add_column("Speaker", style="bold", width=12)
        table.add_column("Message / Context", style="white")

        for e in entries:
            role = e.get("role", "unknown")
            if role == "user":
                label = "[cyan]👤 USER[/cyan]"
                cmd = f"[dim](cmd: {e['command_name']})[/dim] " if e.get("command_name") else ""
                content = f"{cmd}{e.get('content', '')}"
            else:
                label = f"[{GHOST_MOODS.get(e.get('mood', 'cursed'), GHOST_MOODS['cursed'])['color']}]👻 GHOST[/{GHOST_MOODS.get(e.get('mood', 'cursed'), GHOST_MOODS['cursed'])['color']}]"
                content = e.get("content", "")
            table.add_row(e.get("timestamp", ""), label, content)

        console.print(table)
        console.print("[dim]Type 'save' to export this transcript to a file, or 'clear_memory' to erase it.[/dim]\n")

    def print_shutdown(self) -> None:
        """Play farewell animation when user exits."""
        mood_meta = GHOST_MOODS.get(self.config.mood, GHOST_MOODS["cursed"])
        console.print(f"\n[italic {mood_meta['color']}]\"You close the shell... but I remain in the lingering glow of your phosphors.\"[/italic {mood_meta['color']}]")
        console.print(ASCII_EXIT)
        console.print("[bold green]Haunted Terminal released. Until we meet in the machine again... 👻[/bold green]\n")
