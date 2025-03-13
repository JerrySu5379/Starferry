from typing import Optional
from fastapi import APIRouter, Request, Form
from pydantic import BaseModel
from src.services.openai_service import OpenAIService
from src.services.gemini_service import GeminiService
from src.services.grok_service import GrokService
import asyncio
from src.utils.ip_tracker import track_ip  # Updated import

class BingoRequest(BaseModel):
    prompt: str
    service: str

class BingoResponse(BaseModel):
    items: Optional[str]
    error: Optional[str] = None

router = APIRouter()

# Initialize services
openai_service = OpenAIService()
gemini_service = GeminiService()
grok_service = GrokService()
SYSTEM_PROMPT = (
    "Be a bingo game designer, generate 30 items that will be used in a Bingo game regarding the prompt, which will be input later. \n"
    "Your output should be only the 25 items, separated by the '|' character, do not output anything else before the item list starts, \n"
    "and do not wrap them with any other syntax. Try your best to generate exactly 25 items. Output by using the language of the prompt."
)

async def generate_bingo_items(prompt: str, service: str) -> Optional[str]:
    if service.lower() == "openai":
        return await asyncio.to_thread(openai_service._create_completion, SYSTEM_PROMPT, prompt, conversation_history=[])
    elif service.lower() == "gemini":
        return await asyncio.to_thread(gemini_service._create_completion, SYSTEM_PROMPT, prompt, conversation_history=[])
    elif service.lower() == "grok":
        return await asyncio.to_thread(grok_service._create_completion, SYSTEM_PROMPT, prompt, model="grok-2-latest", conversation_history=[])
    else:
        return None

@router.post("/bingo", response_model=BingoResponse)
async def generate_bingo(
    request: Request,
    prompt: str = Form(...),
    service: str = Form(...)
):
    client_ip = request.client.host

    # Use the centralized rate limiter function
    if not track_ip(client_ip):
        return BingoResponse(items=None, error="API usage limit exceeded. Please try again later.")

    # Generate bingo items using the appropriate service
    result = await generate_bingo_items(prompt, service)
    if result is None:
        return BingoResponse(items=None, error="Invalid service specified. Use 'openai', 'gemini', or 'grok'.")
    return BingoResponse(items=result)