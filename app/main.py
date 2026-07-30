from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from .models import PatchInput, SummaryResponse
from .summarize import summarize_patch

app = FastAPI(title="Game Patch Copilot API")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://game-patch-copilot-web.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/summarize", response_model=SummaryResponse)
def summarize(inp: PatchInput) -> Any:
    result = summarize_patch(inp.game_id, inp.text, inp.custom_instructions)
    return SummaryResponse(**result)