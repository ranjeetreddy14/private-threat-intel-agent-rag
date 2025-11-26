from openai import OpenAI
from .config import LLAMA_API_BASE

class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url=LLAMA_API_BASE, api_key="sk-no-key-required")

    def chat_completion(self, messages, temperature=0.7, max_tokens=1024, stream=True):
        """
        Generates a chat completion from the local LLM.
        """
        try:
            response = self.client.chat.completions.create(
                model="qwen", # Model name doesn't strictly matter for local llama-server usually, but good to set
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            print(f"Error querying LLM: {e}")
            return None
