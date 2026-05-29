import pyperclip
import json
import os
import subprocess
import shutil
import pyfiglet
from datetime import datetime
import time
import urllib.request
import ssl
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markup import escape

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # always points to libexec
HISTORY_FILE = os.path.join(SCRIPT_DIR, "clipboard_history.json")  # fixed: was relative
CURRENT_VERSION = "v2.0.0"
REPO_URL = "https://api.github.com/repos/Codemaster-AR/clipboard-text-lightweight/releases/latest"
console = Console()

# --- Update Checker ---
def check_for_updates():
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(
            REPO_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Clipboard-Lite-Update-Checker)'}
        )
        with urllib.request.urlopen(req, context=context, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").strip()
                if latest_version and latest_version != CURRENT_VERSION:
                    return f"[bold yellow]Update Available![/bold yellow] (Current: {CURRENT_VERSION} -> Latest: [bold green]{latest_version}[/bold green])\nRun 'brew upgrade clipboard-lightweight' to update!"
                else:
                    return f"[green]System up to date[/green] ({CURRENT_VERSION})"
    except urllib.error.URLError as e:
        return f"[dim red]Connection failed: {e.reason}[/dim red]"
    except Exception as e:
        return f"[dim red]Update check error: {str(e)}[/dim red]"
    return f"[dim]Version: {CURRENT_VERSION}[/dim]"

# --- Shared UI Helpers ---
def get_header():
    ascii_art = pyfiglet.figlet_format("Clipboard Lite", font="slant")
    return f"[bold cyan]{ascii_art}[/bold cyan]"

# --- Text-Based Logic ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                history = []
                for item in data:
                    if isinstance(item, str):
                        history.append({"text": item, "timestamp": datetime.now().isoformat()})
                    elif isinstance(item, dict):
                        txt = item.get('text') or item.get('content') or ""
                        ts = item.get('timestamp') or datetime.now().isoformat()
                        history.append({"text": str(txt), "timestamp": str(ts)})
                return history
        except (json.JSONDecodeError, Exception):
            return []
    return []

def save_history(history):
    try:
        if not isinstance(history, list):
            history = []
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        console.print(f"[red]Error saving history: {e}[/red]")

def add_to_history(text):
    if not text or not str(text).strip():
        return
    text = str(text)
    history = load_history()
    if history and history[0].get('text') == text:
        return
    entry = {"timestamp": datetime.now().isoformat(), "text": text}
    history.insert(0, entry)
    save_history(history[:50])

def format_cli_timestamp(timestamp_str):
    if not timestamp_str or not isinstance(timestamp_str, str) or timestamp_str == "Unknown":
        return "Unknown"
    try:
        if 'T' in timestamp_str:
            ts = timestamp_str.replace('Z', '').split('.')[0]
            dt = datetime.fromisoformat(ts)
        else:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %H:%M:%S")
    except Exception:
        return timestamp_str

def show_history():
    history = load_history()
    if not history:
        console.print("[yellow]History is empty.[/yellow]")
        return
    console.print("\n[bold blue]Note:[/bold blue] This table shows your [italic]past[/italic] clipboard contents.")
    console.print("[dim]If you see 'TypeError' or 'Traceback' below, they are records of previous crashes that you copied.[/dim]\n")
    table = Table(title="Clipboard History", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Date/Time", style="cyan")
    table.add_column("Content", style="green")
    for idx, item in enumerate(history):
        if not isinstance(item, dict):
            continue
        text = str(item.get('text', ""))
        timestamp = str(item.get('timestamp', "Unknown"))
        formatted_time = str(format_cli_timestamp(timestamp))
        clean_text = text.replace('\n', ' ').replace('\r', '').strip()
        content_display = clean_text[:50] + ("..." if len(clean_text) > 50 else "")
        table.add_row(str(idx), formatted_time, escape(content_display))
    console.print(table)

def run_text_version():
    while True:
        console.clear()
        console.print(get_header())
        console.print(Panel("[bold white]1.[/bold white] Check Current\n[bold white]2.[/bold white] View History\n[bold white]3.[/bold white] Re-copy Item\n[bold white]4.[/bold white] Delete Item\n[bold white]5.[/bold white] Clear All\n[bold white]6.[/bold white] Back to Launcher", title="Menu", expand=False))
        choice = str(console.input("[bold yellow]Select an option:[/bold yellow] ")).strip()
        if choice == '1':
            current = str(pyperclip.paste())
            console.print("Current clipboard content:", style="bold white")
            console.print("-" * 20)
            console.print(escape(current))
            console.print("-" * 20)
            if console.input("\nSave this to history? (y/n): ").lower() == 'y':
                add_to_history(current)
                console.print("[green]Saved to history![/green]")
                time.sleep(1)
        elif choice == '2':
            show_history()
            console.input("\nPress Enter to return to menu...")
        elif choice == '3':
            show_history()
            try:
                user_input = console.input("Enter ID to re-copy (or Enter to cancel): ")
                if not user_input.strip():
                    continue
                idx = int(user_input)
                history = load_history()
                if 0 <= idx < len(history):
                    target_text = str(history[idx].get('text', ""))
                    pyperclip.copy(target_text)
                    console.print(f"[green]Copied ID {idx} to clipboard![/green]")
                else:
                    console.print("[red]Error: ID not found.[/red]")
            except ValueError:
                console.print("[red]Error: Please enter a valid number.[/red]")
            time.sleep(1.5)
        elif choice == '4':
            show_history()
            try:
                user_input = console.input("Enter ID to delete (or Enter to cancel): ")
                if not user_input.strip():
                    continue
                idx = int(user_input)
                history = load_history()
                if 0 <= idx < len(history):
                    history.pop(idx)
                    save_history(history)
                    console.print(f"[red]Deleted ID {idx}.[/red]")
                else:
                    console.print("[red]Error: ID not found.[/red]")
            except ValueError:
                console.print("[red]Error: Please enter a valid number.[/red]")
            time.sleep(1.5)
        elif choice == '5':
            confirm = console.input("Are you sure you want to clear EVERYTHING? (y/n): ")
            if confirm.lower() == 'y':
                save_history([])
                console.print("[bold red]History cleared![/bold red]")
            time.sleep(1)
        elif choice == '6':
            break

# --- GUI Launcher Logic (Cross-Platform) ---
def run_gui_version():
    if not shutil.which("node"):
        console.print("[red]Error: 'node' (Node.js) is not installed.[/red]")
        return

    # Fixed: use SCRIPT_DIR so paths resolve to libexec, not user's home
    node_modules = os.path.join(SCRIPT_DIR, "node_modules")
    if not os.path.exists(node_modules):
        console.print("[yellow]Installing dependencies...[/yellow]")
        subprocess.run(["npm", "install"], check=True, cwd=SCRIPT_DIR, shell=(os.name == 'nt'))

    electron_entry = os.path.join(SCRIPT_DIR, "node_modules", "electron", "cli.js")

    console.print("[bold blue]Launching Electron (Background)...[/bold blue]")
    try:
        subprocess.Popen(
            ["node", electron_entry, "."],
            cwd=SCRIPT_DIR,  # fixed: was missing cwd
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        console.print("[green]GUI launched successfully! Returning to menu...[/green]")
    except Exception as e:
        console.print(f"[red]Failed to launch: {e}[/red]")

    time.sleep(2)

# --- Main Entry Point ---
def main():
    console.clear()
    console.print(get_header())
    console.print("[dim cyan]Checking for updates...[/dim cyan]")
    update_status = check_for_updates()
    while True:
        console.clear()
        console.print(get_header())
        console.print(update_status)
        console.print()
        console.print(Panel("Choose interface:", title="Launcher", expand=False))
        console.print("[1] Text-Based CLI\n[2] Electron GUI\n[3] Exit")
        choice = console.input("\n[bold yellow]Selection: [/bold yellow]")
        if choice == '1':
            run_text_version()
        elif choice == '2':
            run_gui_version()
        elif choice == '3':
            break

if __name__ == "__main__":
    main()
