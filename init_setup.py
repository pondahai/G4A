import os
import sys
import subprocess
import venv
from pathlib import Path
import json
import urllib.request
import urllib.error

def print_step(msg):
    print(f"\n[\033[94m*\033[0m] {msg}")

def print_success(msg):
    print(f"[\033[92m+\033[0m] {msg}")

def print_warning(msg):
    print(f"[\033[93m!\033[0m] {msg}")

def print_error(msg):
    print(f"[\033[91m-\033[0m] {msg}")

def check_python_version():
    print_step("Checking Python version...")
    if sys.version_info < (3, 10):
        print_error("Python 3.10 or higher is required.")
        sys.exit(1)
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} detected.")

def setup_directories():
    print_step("Setting up G4A directories...")
    # Read config to find skills_dir
    skills_dir = "~/.g4a/skills"
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                skills_dir = config.get("skills_dir", skills_dir)
            except json.JSONDecodeError:
                pass
    
    full_path = Path(os.path.expanduser(skills_dir))
    full_path.mkdir(parents=True, exist_ok=True)
    
    init_file = full_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        
    print_success(f"Skills directory initialized at: {full_path}")

def check_docker():
    print_step("Checking Docker status (for Sandbox)...")
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Docker is running. Sandbox execution is enabled.")
        else:
            print_warning("Docker command found, but daemon might not be running. Sandbox will be disabled.")
    except FileNotFoundError:
        print_warning("Docker is not installed or not in PATH. Sandbox execution will be disabled.")

def check_ollama():
    print_step("Checking local LLM API (Ollama)...")
    config_path = Path("config.json")
    api_url = "http://localhost:11434/api"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                api_url = config.get("api_url", api_url)
            except json.JSONDecodeError:
                pass

    # Basic check to see if we can reach the base URL (removing /api if present)
    base_url = api_url.replace("/api", "")
    try:
        response = urllib.request.urlopen(base_url, timeout=2)
        if response.getcode() == 200:
            print_success(f"Local LLM API reachable at {base_url}.")
    except urllib.error.URLError:
        print_warning(f"Could not connect to LLM API at {base_url}. Ensure Ollama/vLLM is running before starting G4A.")
    except Exception as e:
        print_warning(f"Error checking LLM API: {e}")

def create_venv_and_install():
    print_step("Setting up Virtual Environment and installing dependencies...")
    venv_dir = Path(".venv")
    
    if not venv_dir.exists():
        print("Creating virtual environment '.venv'...")
        venv.create(venv_dir, with_pip=True)
        print_success("Virtual environment created.")
    else:
        print_success("Virtual environment already exists.")

    # Determine pip path
    if os.name == 'nt':
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_exe = venv_dir / "bin" / "pip"

    if pip_exe.exists():
        print("Installing dependencies from requirements.txt...")
        try:
            subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], check=True)
            print_success("Dependencies installed successfully.")
        except subprocess.CalledProcessError:
            print_error("Failed to install dependencies.")
    else:
        print_error(f"Could not find pip executable in {pip_exe}")

def main():
    print("\n" + "="*50)
    print("🚀 G4A (Gemma 4 Agent) Initialization Script 🚀")
    print("="*50)
    
    check_python_version()
    setup_directories()
    check_docker()
    check_ollama()
    create_venv_and_install()
    
    print("\n" + "="*50)
    print("✅ Initialization Complete!")
    print("\nTo start G4A, activate the virtual environment and run main.py:")
    if os.name == 'nt':
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("  python main.py")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
