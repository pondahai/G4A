import sys
from rich.console import Console
from rich.markdown import Markdown
from core.brain_engine import BrainEngine
from agent.evolution_mgr import EvolutionManager

console = Console()

def run_cli(config):
    console.print("[bold green]🚀 Welcome to G4A (Gemma 4 Agent) CLI[/bold green]")
    console.print("Type [bold yellow]/help[/bold yellow] for available commands or start chatting!\n")
    
    brain = BrainEngine(config)
    evo_mgr = EvolutionManager(config, brain)
    evo_mgr.load_skills()

    while True:
        try:
            user_input = console.input("[bold blue]You > [/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Exiting G4A. Goodbye![/bold red]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handle_command(user_input, config, brain, evo_mgr)
            continue

        # Wrap user input in XML tags to prevent prompt injection (basic safety)
        safe_input = f"<user_input>{user_input}</user_input>"
        
        # Determine if we can answer or need a skill, then execute
        try:
            response_generator = brain.stream_chat(safe_input)
            
            console.print("[bold magenta]G4A > [/bold magenta]", end="")
            full_response = ""
            for chunk in response_generator:
                print(chunk, end="", flush=True)
                full_response += chunk
            print()
            
            # Post-process: Check if a new tool generation is needed
            if "NEEDS_NEW_SKILL" in full_response:
                console.print("[bold yellow]🧠 G4A detects a missing capability. Entering Code Generation Mode...[/bold yellow]")
                evo_mgr.generate_and_test_skill(user_input)
                
        except Exception as e:
            console.print(f"\n[bold red]Error connecting to brain: {e}[/bold red]")


def handle_command(command_str: str, config: dict, brain: BrainEngine, evo_mgr: EvolutionManager):
    parts = command_str.split(" ", 1)
    cmd = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/brain":
        if args:
            config["model"] = args
            brain.model = args
            # Actually need to save config, but let's assume it only lives in memory for now or import save_config
            from main import save_config
            save_config(config)
            console.print(f"[green]✅ Model changed to:[/green] {args}")
        else:
            console.print(f"[yellow]Current model:[/yellow] {config['model']}")
            
    elif cmd == "/api":
        if args:
            config["api_url"] = args
            brain.api_url = args
            from main import save_config
            save_config(config)
            console.print(f"[green]✅ API URL changed to:[/green] {args}")
        else:
            console.print(f"[yellow]Current API URL:[/yellow] {config['api_url']}")
            
    elif cmd == "/skills":
        skills = evo_mgr.list_skills()
        if skills:
            console.print("[bold cyan]Available Skills:[/bold cyan]")
            for s in skills:
                console.print(f" - {s}")
        else:
            console.print("[yellow]No skills learned yet.[/yellow]")
            
    elif cmd == "/reset":
        brain.clear_memory()
        console.print("[green]✅ Memory cleared.[/green]")
        
    elif cmd == "/help":
        help_text = """
[bold]Available Commands:[/bold]
  /brain <model>  - Switch the current model.
  /api <url>      - Change the backend API URL.
  /skills         - List all currently learned skills.
  /reset          - Clear conversation memory.
  /help           - Show this message.
        """
        console.print(help_text)
    else:
        console.print(f"[bold red]Unknown command:[/bold red] {cmd}")
