import os
import sys
import importlib.util
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from core.safety import check_code_safety, SafetyError
from agent.sandbox import Sandbox

console = Console()

class EvolutionManager:
    def __init__(self, config, brain_engine):
        self.config = config
        self.brain = brain_engine
        
        # Resolve skills directory path
        skills_dir_raw = config.get("skills_dir", "~/.g4a/skills")
        self.skills_dir = Path(os.path.expanduser(skills_dir_raw))
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure __init__.py exists for importability
        init_file = self.skills_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        # Add skills_dir's parent to sys.path so we can import 'skills.xyz'
        parent_dir = str(self.skills_dir.parent)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)

        self.loaded_skills = {}
        self.sandbox = Sandbox()

    def load_skills(self):
        """Dynamically load all .py files in skills directory."""
        for file in self.skills_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue
                
            skill_name = file.stem
            try:
                spec = importlib.util.spec_from_file_location(skill_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_skills[skill_name] = module
                console.print(f"[dim green]Loaded skill: {skill_name}[/dim green]")
            except Exception as e:
                console.print(f"[dim red]Failed to load skill {skill_name}: {e}[/dim red]")

    def list_skills(self):
        return list(self.loaded_skills.keys())

    def generate_and_test_skill(self, user_request: str):
        prompt = f"""
        You are in Code Generation Mode.
        The user asked for: "{user_request}"
        This task cannot be fulfilled natively. Please write a Python script that ACTUALLY performs the requested computation, fetches the real data, or executes the system action.
        DO NOT hardcode, hallucinate, or simulate the final result.
        
        CRITICAL SECURITY REQUIREMENTS:
        1. Output ONLY valid Python code within a ```python block.
        2. DO NOT use 'os', 'subprocess', 'sys', or 'shutil' under any circumstances. They are blocked by the AST scanner. 
           (Tip: Use 'urllib.request', 'requests', 'math', etc. instead.)
        3. Do not use 'eval', 'exec', or 'open'.
        4. The code must define a function called `run_skill()` that executes the core logic.
        5. At the bottom of the script, include: `if __name__ == "__main__": print(run_skill())`
        6. Make it robust and modular.
        """
        
        console.print("[yellow]🧠 Brain is generating new code...[/yellow]")
        generator = self.brain.stream_chat(prompt)
        
        full_response = ""
        for chunk in generator:
            full_response += chunk
            
        # Extract code block
        code = self._extract_code(full_response)
        if not code:
            console.print("[red]❌ Failed to extract Python code from response.[/red]")
            return

        console.print("\n[bold cyan]Generated Code:[/bold cyan]")
        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)

        # Human-in-the-loop (HITL)
        confirm = console.input("\n[bold yellow]Do you approve this code for execution and saving? (y/N) > [/bold yellow]").strip().lower()
        if confirm != 'y':
            console.print("[red]❌ Code rejected by user.[/red]")
            return

        # AST Safety Check
        try:
            console.print("[yellow]🛡️ Running AST Safety Scan...[/yellow]")
            check_code_safety(code)
            console.print("[green]✅ Safety scan passed.[/green]")
        except SafetyError as e:
            console.print(f"[bold red]❌ Safety scan failed:[/bold red] {e}")
            self._self_refine(user_request, code, str(e))
            return

        # Sandbox Execution
        if self.sandbox.client:
            console.print("[yellow]📦 Executing in Docker Sandbox...[/yellow]")
            result = self.sandbox.execute_code(code)
            if not result["success"]:
                console.print(f"[bold red]❌ Execution failed in sandbox:[/bold red]\n{result['output']}")
                self._self_refine(user_request, code, result['output'])
                return
            console.print(f"[green]✅ Execution successful:[/green]\n{result['output']}")
        else:
            console.print("[yellow]⚠️ Docker not available, executing locally (Warning: Unsandboxed)...[/yellow]")
            import subprocess
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = Path(temp_dir) / "skill.py"
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(code)
                try:
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, encoding="utf-8", timeout=10, env=env)
                    if res.returncode != 0:
                        console.print(f"[bold red]❌ Execution failed locally:[/bold red]\n{res.stderr}")
                        self._self_refine(user_request, code, res.stderr)
                        return
                    console.print(f"[green]✅ Execution successful:[/green]\n{res.stdout}")
                except Exception as e:
                    console.print(f"[bold red]❌ Execution failed:[/bold red] {e}")
                    return

        # Save to skill library
        skill_name = self._generate_skill_name(user_request)
        skill_path = self.skills_dir / f"{skill_name}.py"
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        console.print(f"[bold green]✅ New skill saved as {skill_path}[/bold green]")
        self.load_skills()

    def _extract_code(self, response: str) -> str:
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                return parts[1].strip()
        return ""

    def _self_refine(self, original_request: str, failed_code: str, error_msg: str):
        console.print("[yellow]🔄 Initiating Self-Refinement based on error...[/yellow]")
        refine_prompt = f"""
        I tried to run your previous code for the task: "{original_request}"
        However, it failed with the following error:
        {error_msg}
        
        Please rewrite the python code to fix this issue. Return ONLY the valid Python code in a ```python block.
        """
        # Since it's YOLO mode, let's just make one attempt to refine, or just log it.
        # Calling generate_and_test_skill recursively might cause infinite loops, so we stop here for the MVP.
        console.print("[red]Self-refinement loop triggered. (Not fully implemented in MVP to prevent loops)[/red]")

    def _generate_skill_name(self, request: str) -> str:
        # Try to ask LLM for a good name
        console.print("[dim]Thinking of a good name for the skill...[/dim]")
        llm_name = self.brain.generate_short_name(request)
        if llm_name:
            return llm_name
            
        # Fallback simple slugify
        clean = "".join(c if c.isalnum() else "_" for c in request.lower())
        # Trim multiple underscores
        import re
        clean = re.sub(r'_+', '_', clean).strip('_')
        return f"skill_{clean[:20]}"
