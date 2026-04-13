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
            skills_str = ", ".join(evo_mgr.list_skills()) if evo_mgr.list_skills() else "None"
            enhanced_input = f"<system_context>\nAvailable Skills: {skills_str}\n</system_context>\n{safe_input}"
            
            response_generator = brain.stream_chat(enhanced_input)
            
            console.print("[bold magenta]G4A > [/bold magenta]", end="")
            full_response = ""
            for chunk in response_generator:
                print(chunk, end="", flush=True)
                full_response += chunk
            print()
            
            # Post-process: Check if a new tool generation is needed
            if "NEEDS_NEW_SKILL" in full_response:
                console.print("[bold yellow]🧠 G4A detects a missing capability. Entering Code Generation Mode...[/bold yellow]")
                result = evo_mgr.generate_and_test_skill(user_input)
                if result:
                    console.print("\n[bold green]🎯 Final Execution Result:[/bold green]")
                    console.print(result)
                    brain.history.append({"role": "system", "content": f"The newly generated skill returned this result: {result}"})
                    
                    # Ask LLM to summarize the result for the user
                    console.print("\n[bold magenta]G4A > [/bold magenta]", end="")
                    summary_generator = brain.stream_chat("Skill executed successfully. Please summarize the result for the user naturally based on the data above.")
                    for chunk in summary_generator:
                        print(chunk, end="", flush=True)
                    print()
            
            elif "EXECUTE_SKILL:" in full_response:
                import re
                match = re.search(r'EXECUTE_SKILL:\s*([a-zA-Z0-9_]+)', full_response)
                if match:
                    skill_name = match.group(1)
                    console.print(f"\n[bold yellow]⚙️ Executing existing skill: {skill_name}...[/bold yellow]")
                    result = evo_mgr.execute_skill(skill_name)
                    console.print("\n[bold green]🎯 Raw Execution Result:[/bold green]")
                    console.print(result)
                    brain.history.append({"role": "system", "content": f"The skill {skill_name} returned this result: {result}"})
                    
                    # Ask LLM to summarize the result for the user
                    console.print("\n[bold magenta]G4A > [/bold magenta]", end="")
                    summary_generator = brain.stream_chat("Skill executed successfully. Please summarize the raw result for the user naturally based on the data above.")
                    for chunk in summary_generator:
                        print(chunk, end="", flush=True)
                    print()
                
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
            
    elif cmd == "/apikey":
        if args:
            config["api_key"] = args
            brain.api_key = args
            from main import save_config
            save_config(config)
            console.print(f"[green]✅ API Key updated.[/green]")
        else:
            masked_key = config.get('api_key', '')
            if masked_key:
                masked_key = masked_key[:4] + "*" * (len(masked_key) - 8) + masked_key[-4:] if len(masked_key) > 8 else "****"
            console.print(f"[yellow]Current API Key:[/yellow] {masked_key if masked_key else 'Not set'}")
            
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
  /apikey <key>   - Set the API Key for authentication.
  /skills         - List all currently learned skills.
  /reset          - Clear conversation memory.
  /help           - Show this message.
        """
        console.print(help_text)
    else:
        console.print(f"[bold red]Unknown command:[/bold red] {cmd}")
