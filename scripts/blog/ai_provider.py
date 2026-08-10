import os
import requests

class AIProvider:
    @staticmethod
    def get_provider():
        provider = os.getenv("AI_PROVIDER", "openai").lower()
        if provider not in ["openai", "anthropic"]:
            if os.getenv("ANTHROPIC_API_KEY"):
                return "anthropic"
            return "openai"
        return provider

    def generate(self, system_prompt, user_prompt, temperature=0.7):
        provider = self.get_provider()
        if provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt, temperature)
        else:
            return self._generate_openai(system_prompt, user_prompt, temperature)

    def _generate_openai(self, system_prompt, user_prompt, temperature):
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API error ({response.status_code}): {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _generate_anthropic(self, system_prompt, user_prompt, temperature):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Anthropic API error ({response.status_code}): {response.text}")
            
        result = response.json()
        return result["content"][0]["text"]
