import json
import time
import threading
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

import torch
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

# ---------------------------------------------------------------------------
# Config — same values as your simple-qwen3.py
# ---------------------------------------------------------------------------
#MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_ID = "Qwen/Qwen3-0.6B"
DEVICE = "cpu"
DTYPE  = torch.float32

# ---------------------------------------------------------------------------
# Load model ONCE at startup (not on every request)
# ---------------------------------------------------------------------------
model     = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    print(f"Loading {MODEL_ID} on {DEVICE} ({DTYPE}) — be patient…")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        device_map=DEVICE,
        low_cpu_mem_usage=True,
    )
    model.eval()
    print("Model ready ✓")
    yield  # server runs here


app = FastAPI(title="Qwen3 OpenAI-compatible API", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = MODEL_ID
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float       = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int    = Field(default=3000, ge=1)
    stream: bool       = False

# ---------------------------------------------------------------------------
# Helper: apply chat template (same as simple-qwen3.py)
# ---------------------------------------------------------------------------
def build_prompt(messages: List[Message]) -> str:
    return tokenizer.apply_chat_template(
        [m.model_dump() for m in messages],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------
@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{
            "id": MODEL_ID,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local",
        }],
    }

# ---------------------------------------------------------------------------
# POST /v1/chat/completions
# ---------------------------------------------------------------------------
@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    prompt = build_prompt(req.messages)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    prompt_tokens = inputs.input_ids.shape[-1]

    gen_kwargs = dict(
        **inputs,
        max_new_tokens=req.max_tokens,
        do_sample=True,
        temperature=req.temperature,
        top_p=req.top_p,
        pad_token_id=tokenizer.eos_token_id,
    )

    # ---- Streaming --------------------------------------------------------
    if req.stream:
        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        gen_kwargs["streamer"] = streamer

        # model.generate() runs in background; we iterate tokens here
        thread = threading.Thread(target=model.generate, kwargs=gen_kwargs, daemon=True)
        thread.start()

        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())

        def event_stream():
            completion_tokens = 0
            for token in streamer:
                completion_tokens += 1
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": token},
                        "finish_reason": None,
                    }],
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final chunk
            final = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": req.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
            yield f"data: {json.dumps(final)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ---- Non-streaming ----------------------------------------------------
    with torch.inference_mode():
        output_ids = model.generate(**gen_kwargs)

    new_ids = output_ids[0][prompt_tokens:]
    completion_text   = tokenizer.decode(new_ids, skip_special_tokens=True)
    completion_tokens = len(new_ids)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": completion_text},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
