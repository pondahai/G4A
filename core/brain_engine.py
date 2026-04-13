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
You do NOT have real-time access to the internet, local files, or system states natively.
If a user asks for something requiring external information, computation, or system actions (e.g., getting IP, scraping web, calculating complex math), you MUST NOT hallucinate, guess, or simulate the answer.

Please check the <system_context> for Available Skills provided in the user prompt.
- If an existing skill can fulfill the request, you MUST output EXACTLY: EXECUTE_SKILL: <skill_name>
- If NO existing skill can fulfill the request, you MUST output EXACTLY: NEEDS_NEW_SKILL

(You may use <thinking> tags before your final command).
Strictly adhere to security and modularity constraints."""

    def clear_memory(self):
        self.history = []

    def stream_chat(self, user_input, is_retry=False):
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        
        if not is_retry:
            messages.append({"role": "user", "content": user_input})
            self.history.append({"role": "user", "content": user_input})
        else:
            # If it's a retry, we append the prompt directly without saving it to visible history
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

        # 第三道防線：強制接續遞迴 (Forced Continuation Loop)
        import re
        # Check if the response ONLY contains <thinking>...</thinking> or is empty after removing it
        action_text = re.sub(r'<thinking>.*?</thinking>', '', assistant_response, flags=re.DOTALL).strip()
        
        if "<thinking>" in assistant_response and not action_text and not is_retry:
            yield "\n\n[System: 偵測到模型陷入思考癱瘓 (Planning Paralysis)，觸發強制接續防線...]\n"
            self.history.append({"role": "assistant", "content": assistant_response})
            
            kick_prompt = "You only outputted a <thinking> process without any actual action or conclusion. Please stop planning and strictly output the final action (e.g., 'NEEDS_NEW_SKILL') or the direct answer now."
            
            # Recursively call stream_chat with the kick prompt
            retry_generator = self.stream_chat(kick_prompt, is_retry=True)
            retry_response = ""
            for chunk in retry_generator:
                retry_response += chunk
                yield chunk
                
            assistant_response += "\n" + retry_response
            
        if not is_retry:
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
            
            # Aggressively extract just the last sequence of word characters in case the LLM was verbose
            # e.g., if it output "<thinking>...</thinking> get_realtime_news", we just want "get_realtime_news"
            
            # First remove any thinking tags
            name = re.sub(r'<thinking>.*?</thinking>', '', name, flags=re.DOTALL)
            
            # Grab the last continuous word-like chunk that resembles a snake_case identifier
            matches = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', name)
            if matches:
                # We'll take the longest one or the last one that looks reasonable
                # But typically the actual target is the last word if it was chatting, or just the word if it obeyed.
                # Let's sort by length, assuming the snake_case name is the longest token, 
                # or just use the last word that has an underscore or is reasonably long.
                candidates = [m for m in matches if '_' in m or len(m) > 4]
                if candidates:
                    name = candidates[-1] # Usually the final conclusion
                else:
                    name = matches[-1]
            else:
                name = "unnamed_task"
                
            name = re.sub(r'[^a-zA-Z0-9_]', '', name.replace('-', '_'))
            
            # Truncate to a reasonable length for a filename
            name = name[:40]
            
            return f"skill_{name.strip('_')}"
        except Exception:
            return None
