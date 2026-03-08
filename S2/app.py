# Run:
#   uvicorn app:app --host 0.0.0.0 --port 8000
#
# Models:
#   curl http://localhost:8000/v1/models
#
# Chat (non-streaming):
#   curl http://localhost:8000/v1/chat/completions \
#     -H "Content-Type: application/json" \
#     -d '{"model":"qwen3-1.7b","messages":[{"role":"user","content":"Hello!"}]}'
#
# Chat (streaming):
#   curl http://localhost:8000/v1/chat/completions \
#     -H "Content-Type: application/json" \
#     -N \
#     -d '{"model":"qwen3-1.7b","messages":[{"role":"user","content":"Explain FastAPI briefly."}],"stream":true}'

import json
import time
import uuid
from threading import Thread
from typing import Any, Dict, List, Literal, Optional

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

MODEL_NAME = "qwen3-1.7b"
MODEL_ID = "Qwen/Qwen3-1.7B"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 200
    stream: Optional[bool] = False


app = FastAPI(title="OpenAI-Compatible Local Qwen Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev: allow requests from file://, localhost, etc.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load once at process start.
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
model.eval()


def openai_error(message: str, code: str = "invalid_request_error", status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "message": message,
                "type": code,
                "param": None,
                "code": None,
            }
        },
    )


def build_prompt(messages: List[ChatMessage]) -> str:
    raw_messages = [{"role": m.role, "content": m.content} for m in messages]
    return tokenizer.apply_chat_template(
        raw_messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    if req.model != MODEL_NAME:
        return openai_error(f"Model '{req.model}' not found. Available model: '{MODEL_NAME}'.", code="model_not_found", status=404)

    prompt = build_prompt(req.messages)
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"]
    prompt_tokens = int(input_ids.shape[-1])

    max_new_tokens = int(req.max_tokens or 200)
    temperature = float(req.temperature if req.temperature is not None else 0.7)

    generation_kwargs = {
        "input_ids": input_ids,
        "attention_mask": inputs.get("attention_mask"),
        "max_new_tokens": max_new_tokens,
        "do_sample": True,
        "temperature": temperature,
        "top_p": 0.9,
        "pad_token_id": tokenizer.eos_token_id,
    }

    created = int(time.time())
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"

    if not req.stream:
        with torch.no_grad():
            output_ids = model.generate(**generation_kwargs)

        new_token_ids = output_ids[0, prompt_tokens:]
        assistant_text = tokenizer.decode(new_token_ids, skip_special_tokens=True)
        completion_tokens = int(new_token_ids.shape[-1])

        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": assistant_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    def stream_events():
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        thread = Thread(
            target=model.generate,
            kwargs={**generation_kwargs, "streamer": streamer},
            daemon=True,
        )
        thread.start()

        first_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(first_chunk)}\n\n"

        for text in streamer:
            if not text:
                continue
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": MODEL_NAME,
                "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"

        final_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
