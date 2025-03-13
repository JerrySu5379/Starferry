import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from src.utils import format_conversation_history

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.default_params = {
            "temperature": 1,
            "max_tokens": 256,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "response_format": {"type": "text"}
        }

    def _create_completion(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "gpt-4o-mini",
        conversation_history: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        try:
            params = {**self.default_params, **kwargs}
            messages = [
                {
                    "role": "system",
                    "content": [{"text": system_prompt}]
                }
            ]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append(
                {
                    "role": "user",
                    "content": [{"text": user_prompt, "type": "text"}]
                }
            )
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **params
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in OpenAI completion: {str(e)}")
            return None