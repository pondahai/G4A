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

        # 根據 URL 判斷是 OpenAI-compatible (vLLM) 還是 Ollama
        if "v1" in self.api_url:
            endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
            is_openai = True
        else:
            endpoint = f"{self.api_url.rstrip('/')}/chat"
            is_openai = False
            
        response = requests.post(endpoint, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        assistant_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                
                # 處理 OpenAI SSE 格式 (data: {...})
                if decoded_line.startswith("data: "):
                    decoded_line = decoded_line[6:]
                if decoded_line.strip() == "[DONE]":
                    break
                    
                try:
                    data = json.loads(decoded_line)
                    if is_openai:
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                assistant_response += content
                                yield content
                    else:
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            assistant_response += content
                            yield content
                except json.JSONDecodeError:
                    pass

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": assistant_response})

    def generate_short_name(self, text: str) -> str:
        messages = [
            {"role": "system", "content": "You are a naming assistant. Given a task description, output ONLY a short, concise, snake_case Python valid identifier (e.g., get_public_ip). Do NOT include .py extension. No markdown, no explanations."},
            {"role": "user", "content": text}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"

        if "v1" in self.api_url:
            endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
            is_openai = True
        else:
            endpoint = f"{self.api_url.rstrip('/')}/chat"
            is_openai = False
            
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if is_openai:
                name = data["choices"][0]["message"]["content"].strip()
            else:
                name = data["message"]["content"].strip()
            
            import re
            name = re.sub(r'[^a-zA-Z0-9_]', '', name.replace('-', '_'))
            return f"skill_{name.strip('_')}"
        except Exception:
            return None
