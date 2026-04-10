import json
import requests
import sys

class BrainEngine:
    def __init__(self, config):
        self.model = config.get("model", "gemma4")
        self.api_url = config.get("api_url", "http://localhost:11434/api")
        self.api_key = config.get("api_key", "")
        self.history = []
        
        # System prompt from spec
        self.system_prompt = """You are G4A (Gemma 4 Agent), an advanced AI assistant capable of self-evolution.
You can write Python code to create new tools when existing tools are insufficient.
If a user asks for something you cannot do natively, output 'NEEDS_NEW_SKILL' and wait for Code Generation Mode to start.
Use <thinking>...</thinking> tags to show your chain of thought before providing a final answer.
Strictly adhere to security and modularity constraints."""

    def clear_memory(self):
        self.history = []

    def stream_chat(self, user_input):
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_input})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
            
        response = requests.post(f"{self.api_url}/chat", json=payload, headers=headers, stream=True)
        response.raise_for_status()

        assistant_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                try:
                    data = json.loads(decoded_line)
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        assistant_response += content
                        yield content
                except json.JSONDecodeError:
                    pass

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": assistant_response})
