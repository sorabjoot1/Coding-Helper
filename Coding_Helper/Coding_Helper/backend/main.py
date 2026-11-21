from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import get_settings
from .llm import LLMError, chat_completion

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, list[dict[str, str]]] = {}
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

Mode = Literal["generate", "explain", "debug", "optimize", "fix"]

MODE_INSTRUCTIONS = {
    "generate": (
        "Generate a complete, runnable solution. Include code blocks with language tags, "
        "brief setup notes, and example usage when useful."
    ),
    "explain": (
        "Explain the provided code in simple language. Cover purpose, flow, and important lines. "
        "Use short paragraphs and bullet points."
    ),
    "debug": (
        "Detect bugs and errors in the provided code. Explain the root cause, then provide a fixed "
        "complete version of the code."
    ),
    "optimize": (
        "Improve and optimize the provided code for readability, performance, and best practices. "
        "Show the improved code and list the improvements made."
    ),
    "fix": (
        "Answer the programming question clearly. Include examples or code snippets when helpful."
    ),
}


class AssistRequest(BaseModel):
    mode: Mode = "generate"
    language: str = Field(default="python", min_length=1, max_length=40)
    prompt: str = Field(..., min_length=1, max_length=8000)
    code: str = Field(default="", max_length=20000)
    session_id: str | None = Field(default=None, max_length=64)


class AssistResponse(BaseModel):
    session_id: str
    mode: Mode
    language: str
    reply: str
    history: list[dict[str, str]]


@app.get("/api/health")
async def health() -> dict:
    configured = bool(settings.openrouter_api_key) and not settings.openrouter_api_key.startswith(
        "your_"
    )
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_configured": configured,
        "model": settings.openrouter_model,
    }


@app.post("/api/session")
async def create_session() -> dict:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = []
    return {"session_id": session_id}


@app.get("/api/history/{session_id}")
async def get_history(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "history": SESSIONS[session_id]}


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    SESSIONS[session_id] = []
    return {"session_id": session_id, "cleared": True}


@app.post("/api/assist", response_model=AssistResponse)
async def assist(payload: AssistRequest) -> AssistResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    history = SESSIONS.setdefault(session_id, [])

    instruction = MODE_INSTRUCTIONS[payload.mode]
    user_parts = [
        f"Mode: {payload.mode}",
        f"Language: {payload.language}",
        f"Task/Question:\n{payload.prompt.strip()}",
    ]
    if payload.code.strip():
        user_parts.append(f"User code:\n```{payload.language}\n{payload.code.strip()}\n```")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert coding assistant. Produce accurate, practical help. "
                f"Current task guidance: {instruction}"
            ),
        }
    ]
    for turn in history[-8:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    user_content = "\n\n".join(user_parts)
    messages.append({"role": "user", "content": user_content})

    try:
        reply = await chat_completion(messages)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    history.append({"role": "user", "content": user_content})
    history.append({"role": "assistant", "content": reply})
    SESSIONS[session_id] = history

    return AssistResponse(
        session_id=session_id,
        mode=payload.mode,
        language=payload.language,
        reply=reply,
        history=history,
    )


@app.get("/")
async def serve_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
