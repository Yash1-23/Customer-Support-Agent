"""FastAPI backend for the refund agent.

Serves the single-page UI and streams the agent's reasoning to the browser as
Server-Sent Events (SSE), so the admin panel shows tool calls and the guard's
verdict live — the "real-time agent reasoning logs" the brief asks for.

Run:
    uvicorn app:app --reload
    # then open http://127.0.0.1:8000
"""

import os
import json

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import agent_graph  # this calls load_dotenv() on import, so GROQ_API_KEY is loaded

app = FastAPI(title="Refund Support Agent")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "groq_key_present": bool(os.environ.get("GROQ_API_KEY"))}


@app.post("/api/chat")
async def chat(request: Request):
    """Take the full conversation, stream back reasoning events + the final reply."""
    body = await request.json()
    history = body.get("messages", [])

    def event_stream():
        try:
            for ev in agent_graph.stream_events(history):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:  # surface errors to the panel instead of dropping the stream
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Sync generator -> Starlette iterates it in a threadpool, so the blocking
    # LLM calls don't block the event loop.
    return StreamingResponse(event_stream(), media_type="text/event-stream")


app.mount("/static", StaticFiles(directory="static"), name="static")