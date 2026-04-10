import os
import json
from pathlib import Path

def load_config():
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "model": "gemma4",
        "api_url": "http://localhost:11434/api",
        "skills_dir": "~/.g4a/skills"
    }

def save_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def main():
    config = load_config()
    from core.cli_manager import run_cli
    run_cli(config)

if __name__ == "__main__":
    main()
