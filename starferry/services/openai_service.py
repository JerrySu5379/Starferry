import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from starferry.utils import format_conversation_history
from fastapi.responses import StreamingResponse

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
    ) -> StreamingResponse:
        try:
            params = {**self.default_params, **kwargs, "stream": True}
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append(
                {
                    "role": "user",
                    "content": user_prompt
                }
            )
            
            def stream_response():
                full_response = ""
                for chunk in self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **params
                ):
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        yield chunk.choices[0].delta.content
                
                yield "[DONE]"
            
            return StreamingResponse(stream_response(), media_type="text/event-stream")
        except Exception as e:
            print(f"Error in OpenAI completion: {str(e)}")
            return StreamingResponse(content="Error: " + str(e), media_type="text/plain")