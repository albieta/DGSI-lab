"""
OpenAI-compatible FastAPI server wrapping Qwen3 1.7B.

Endpoints:
  GET  /v1/models                — list available models
  POST /v1/chat/completions      — non-streaming and streaming completions

Usage:
  uvicorn server:app --host 0.0.0.0 --port 8000
"""

import json
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

import torch
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

# ── Model config ──────────────────────────────────────────────────────────────
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_NAME = "qwen3-1.7b"          # the name clients will use

# Module-level references populated at startup
tokenizer: AutoTokenizer = None   # type: ignore[assignment]
model: AutoModelForCausalLM = None  # type: ignore[assignment]


# ── Startup / shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once when the server starts, release it on shutdown."""
    global tokenizer, model

    print(f"[startup] Loading tokenizer and model from '{MODEL_ID}' …")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.bfloat16,       # half the RAM of float32 (~3.4 GB vs ~6.8 GB)
        low_cpu_mem_usage=True,     # stream weights directly instead of double-buffering
    )
    model.eval()
    print("[startup] Model ready.")

    yield  # server is running

    print("[shutdown] Releasing model.")
    del model
    del tokenizer


app = FastAPI(
    title="Qwen3 OpenAI-Compatible Server",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False


# ── Helper: build the prompt ──────────────────────────────────────────────────
def build_prompt(messages: List[Message]) -> str:
    """Apply the Qwen3 chat template to a list of Message objects."""
    raw = [{"role": m.role, "content": m.content} for m in messages]
    return tokenizer.apply_chat_template(
        raw,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


# ── GET /v1/models ────────────────────────────────────────────────────────────
@app.get("/v1/models")
async def list_models():
    """Return the list of available models (just Qwen3 1.7B)."""
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 1700000000,
                "owned_by": "local",
            }
        ],
    }


# ── POST /v1/chat/completions ─────────────────────────────────────────────────
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Main chat endpoint.

    - stream=false  → full JSON response (OpenAI ChatCompletion format)
    - stream=true   → Server-Sent Events, one chunk per token
    """
    prompt = build_prompt(request.messages)
    inputs = tokenizer(prompt, return_tensors="pt")
    prompt_token_count = inputs["input_ids"].shape[1]

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    # Shared generation kwargs
    gen_kwargs = dict(
        **inputs,
        max_new_tokens=request.max_tokens or 512,
        do_sample=True,
        temperature=max(request.temperature or 0.7, 1e-5),  # avoid 0-temp crash
        top_p=request.top_p or 0.9,
        pad_token_id=tokenizer.eos_token_id,
    )

    # ── Streaming ─────────────────────────────────────────────────────────────
    if request.stream:
        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        gen_kwargs["streamer"] = streamer

        def _generate():
            with torch.no_grad():
                model.generate(**gen_kwargs)

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

        async def event_stream():
            # First chunk carries the role (mirrors OpenAI behaviour)
            role_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(role_chunk)}\n\n"

            for text in streamer:
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": text},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final chunk — empty delta + stop reason
            stop_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [
                    {"index": 0, "delta": {}, "finish_reason": "stop"}
                ],
            }
            yield f"data: {json.dumps(stop_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ── Non-streaming ─────────────────────────────────────────────────────────
    with torch.no_grad():
        output_ids = model.generate(**gen_kwargs)

    # Slice off the prompt tokens so we only decode the new content
    new_token_ids = output_ids[0][prompt_token_count:]
    content = tokenizer.decode(new_token_ids, skip_special_tokens=True)
    completion_token_count = len(new_token_ids)

    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": created,
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_token_count,
            "completion_tokens": completion_token_count,
            "total_tokens": prompt_token_count + completion_token_count,
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
