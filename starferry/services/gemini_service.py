import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from fastapi.responses import StreamingResponse
from starferry.utils import format_conversation_history

class GeminiService:
    def __init__(self):
        # Configure the OpenAI client to use Gemini's OpenAI compatibility endpoint.
        self.client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        # Set default parameters for Gemini.
        # Removed frequency_penalty as Gemini API doesn't support it.
        self.default_params = {
            "temperature": 1,
            "max_tokens": 256,
            "top_p": 0.95,
            "presence_penalty": 0,
            "response_format": {"type": "text"}
        }

    def _create_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gemini-2.0-flash-exp",
        conversation_history: List[Dict[str, Any]] = None,
        **kwargs
    ) -> StreamingResponse:
        try:
            # Merge default parameters with any additional keyword arguments and ensure streaming is enabled.
            params = {**self.default_params, **kwargs, "stream": True}
            # Build the messages list.
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_history:
                formatted_history = format_conversation_history(conversation_history)
                messages.extend(formatted_history)
            messages.append({"role": "user", "content": user_prompt})
            
            # Define a generator function that yields each content chunk.
            def stream_response():
                for chunk in self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **params
                ):
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                yield "[DONE]"
            
            # Return a StreamingResponse that will use the generator.
            return StreamingResponse(stream_response(), media_type="text/event-stream")
        except Exception as e:
            print(f"Error in Gemini completion: {str(e)}")
            return StreamingResponse(content="Error: " + str(e), media_type="text/plain")