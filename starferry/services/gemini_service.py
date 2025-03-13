import os
from typing import Optional, List, Dict, Any
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.default_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
        self.chat_session = None

    def _initialize_chat(self, system_instruction: str, model_name: str = "gemini-2.0-flash-exp"):
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.default_config,
            safety_settings=self.safety_settings,
            system_instruction=system_instruction
        )
        self.chat_session = model.start_chat(history=[])
        

    def _create_completion(
        self,
        system_instruction: str,
        user_prompt: str,
        model_name: str = "gemini-2.0-flash",
        conversation_history: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        try:
            from src.utils import format_conversation_history
            
            if not self.chat_session:
                self._initialize_chat(system_instruction, model_name)
            
            if conversation_history:
                formatted_history = format_conversation_history(conversation_history)
                for entry in formatted_history:
                    self.chat_session.send_message(entry["content"][0]["text"], role=entry["role"])
            
            response = self.chat_session.send_message(user_prompt)
            return response.text
        except Exception as e:
            print(f"Error in Gemini completion: {str(e)}")
            return None
        