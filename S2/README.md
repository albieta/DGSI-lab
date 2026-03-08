## Week 2 --- OpenAI-Compatible Server & Context Exploration

# 1. Context Explorer Analysis

## 1.1 Multi-turn Conversation

Provide a screenshot or transcript of a multi-turn conversation using
Context Explorer with a cloud API.

Conversation transcript or screenshot:

Paste conversation here

## 1.2 Messages Array Growth

Explain how the messages array grows during the conversation.

Observations:

- 1: 3 elements
- 2: 5 elements
- 3: 7 elements
- 4: 9 elements

## 1.3 Token Usage Growth

Describe how token usage changes across turns.

Observations:

-   prompt_tokens growth: 14 | 47 | 1982 | 3977
-   completion_tokens growth: 88 | 2045 | 4717 | 281
-   total_tokens behavior: 102 | 2092 | 6699 | 4258

Example usage field:

Paste example usage object here

## 1.4 Role of the System Prompt

Explain the role of the system prompt and how it affects model
responses.

Notes:

-   
-   
-   

Example system prompt used:

Paste system prompt here

------------------------------------------------------------------------

# 2. OpenAI API Concepts

## 2.1 What is the Messages Array?

El Messages Array es una lista ordenada de objetos JSON en la que cada objeto representa un mensaje dentro de la conversación. Cada mensaje incluye el campo "role", que indica el origen del mensaje (instrucción inicial del sistema, una petición del usuario o una respuesta generada por el modelo) y el campo "content", que contiene el texto del mensaje.

Dado que los modelos no disponen de memoria persistente entre llamadas, es necesario enviar el historial de la conversación en cada solicitud a la API. De este modo, en cada petición el modelo recibe el mensaje actual junto con los mensajes anteriores, que se incluyen como contexto para que pueda generar una respuesta coherente.

## 2.2 Streaming vs Non-Streaming Responses

En modo **non-streaming** ("stream": false), el servidor espera a que el modelo genere la respuesta completa y la devuelve de una sola vez como un objeto JSON. El cliente no recibe nada hasta que la respuesta está terminada.

En modo **streaming** ("stream": true), el servidor envía la respuesta token a token conforme el modelo la va generando, sin esperar a tenerla completa. El cliente recibe pequeños fragmentos (llamados `delta`) y los va mostrando progresivamente.


## 2.3 What is Server-Sent Events (SSE)?

SSE es un protocolo web que permite al servidor mantener una conexión HTTP abierta y enviar datos al cliente de forma continua y unidireccional. Cada fragmento de datos se envía como una línea con el formato `data: {...}` seguida de una línea en blanco.

El streaming utiliza SSE para enviar cada token generado como un evento independiente. La secuencia termina con el mensaje especial `data: [DONE]` que indica al cliente que la respuesta ha finalizado.

## 2.4 Why the OpenAI API Became a Standard

OpenAI fue el primer proveedor en popularizar masivamente el acceso a modelos de lenguaje a través de una API bien documentada y fácil de usar.
Ante su éxito, el resto de proveedores decidieron implementar el mismo formato en sus APIs para facilitar la 
compatibilidad.

------------------------------------------------------------------------

# 3. FastAPI Server --- Design and Implementation

## 3.1 Server Architecture

El servidor está implementado con **FastAPI** y expone una API compatible con la librería `openai`. Su estructura es la siguiente:

- **Carga del modelo**: el modelo y el tokenizer se cargan **una sola vez** al arrancar el servidor, usando el mecanismo `lifespan` de FastAPI. Esto evita recargar el modelo en cada petición, lo que sería inviable dado el tamaño del modelo.
- **Endpoints**:
  - `GET /v1/models` — devuelve el modelo disponible en formato OpenAI.
  - `POST /v1/chat/completions` — acepta un array de mensajes y devuelve una respuesta, con soporte para modo streaming y no-streaming.
- **Validación de requests**: se usan modelos Pydantic para validar el JSON entrante (`model`, `messages`, `temperature`, `top_p`, `max_tokens`, `stream`).
- **Conteo de tokens**: se usa `inputs.input_ids.shape[-1]` para contar los tokens del prompt, y `len(new_ids)` para los tokens generados.

------------------------------------------------------------------------

#### 1. Carga del modelo con `lifespan`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        device_map=DEVICE,
        low_cpu_mem_usage=True,
    )
    model.eval()
    print("Model ready ✓")
    yield
```

El modelo se carga una sola vez al arrancar. La palabra clave `global` es necesaria para que las funciones del servidor puedan acceder a las variables `model` y `tokenizer` definidas fuera de `lifespan`.

------------------------------------------------------------------------   

#### 2. Aplicación del chat template

```python
def build_prompt(messages: List[Message]) -> str:
    return tokenizer.apply_chat_template(
        [m.model_dump() for m in messages],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
```

Este helper convierte el array de mensajes al formato de prompt que espera Qwen3, igual que en `simple-qwen3.py` de la semana anterior.

#### 3. Streaming con `TextIteratorStreamer`

```python
streamer = TextIteratorStreamer(
    tokenizer, skip_prompt=True, skip_special_tokens=True
)
gen_kwargs["streamer"] = streamer

thread = threading.Thread(target=model.generate, kwargs=gen_kwargs, daemon=True)
thread.start()

def event_stream():
    for token in streamer:
        chunk = { "choices": [{"delta": {"content": token}, "finish_reason": None}] }
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"

return StreamingResponse(event_stream(), media_type="text/event-stream")
```

`model.generate()` corre en un hilo de fondo mientras el hilo principal itera sobre los tokens conforme se van generando. Cada token se envía como un evento SSE con el formato `data: {...}\n\n`.

------------------------------------------------------------------------

## 3.7 AI Collaboration Log (Vibe Coding Process)

Se utilizó **Claude (Anthropic)** para:
- Generar el código base del servidor `main.py`.
- Diagnosticar errores de configuración del entorno.

Prompt inicial: Build a FastAPI server that wraps a local Qwen3 1.7B transformers model and exposes an OpenAI-compatible API with:
* GET /v1/models
* POST /v1/chat/completions with streaming and non-streaming support using TextIteratorStreamer for token-by-token generation
You can use this code: from transformers import AutoTokenizer, AutoModelForCausalLM import torch
MODEL_ID = "Qwen/Qwen3.5-9B" DEVICE = "cuda" DTYPE = torch.bfloat16
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained( MODEL_ID, torch_dtype=DTYPE, device_map="cuda", low_cpu_mem_usage=True, )
model.eval() print(f"Qwen CLI on {DEVICE} ({DTYPE}) (Ctrl+C to quit)")
while True: try: user = input("\n> ").strip() if not user: continue

| Problema | Causa | Solución |
|---|---|---|
| `ImportError: libcudnn.so.9 not found` | `torch` se instaló con soporte CUDA pero el container no tiene GPU ni librerías CUDA a nivel de sistema | Se reinstalo torch desde el índice CPU (`https://download.pytorch.org/whl/cpu`) |
| `pyproject.toml` con índice CUDA | Al añadir dependencias nvidia manualmente quedó configurado `[[tool.uv.index]] url = .../cu121` | Se limpió el `pyproject.toml` eliminando todas las dependencias `nvidia-*` y cambiando el índice a CPU |
| `torch>=2.10.0` no encontrado | La versión 2.10.0 no existe en ningún índice de PyTorch | Se cambió a `torch>=2.0.0` |
| OOM al cargar Qwen3-1.7B | El container solo tiene 7.5GB de RAM disponibles y el modelo necesita ~4GB, pero Windows consumía el 95% de la RAM total (16GB) | Se usó Qwen3-0.6B (1.5GB) para las pruebas.

------------------------------------------------------------------------

# 4. Testing Evidence

## 4.1 Testing /v1/models

Command:

curl http://localhost:8000/v1/models

Output:

## 4.1 List Models

**Comando:**
```bash
curl http://localhost:8000/v1/models
```

**Respuesta:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen3-0.6B",
      "object": "model",
      "created": 1772931973,
      "owned_by": "local"
    }
  ]
}
```

---

## 4.2 Non-Streaming Completion Test

**Comando:**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is FastAPI?"}
    ],
    "temperature": 0.7
  }'
```

**Respuesta:**
```json
{
  "id": "chatcmpl-9e3051f4e3dd4cbbacc50b7f4255c1f3",
  "object": "chat.completion",
  "created": 1772929983,
  "model": "Qwen/Qwen3-0.6B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "FastAPI is a modern, efficient framework for building APIs in Python. It was developed by FastAPI developers, and it provides a simplified and more robust way to build APIs compared to traditional HTTP frameworks like Flask or Django. FastAPI is built on top of the standard library and uses a simple, concise syntax for defining API endpoints. It's known for being fast, secure, and easy to use."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 81,
    "total_tokens": 109
  }
}
```

------------------------------------------------------------------------

## 4.3 Streaming Completion Test

Command:

curl http://localhost:8000/v1/chat/completions\
-H "Content-Type: application/json"\
-N\
-d '{ "model": "qwen3-1.7b", "messages": \[ {"role": "user", "content":
"Explain Python."} \], "stream": true }'

Output:

C:\Windows\System32>curl -N http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\": \"Qwen/Qwen3-0.6B\", \"messages\": [{\"role\": \"user\", \"content\": \"Explain Python in one paragraph.\"}], \"stream\": true}"
data: {"id": "chatcmpl-2197de5780854e78b007876f2155e638", "object": "chat.completion.chunk", "created": 1772930038, "model": "Qwen/Qwen3-0.6B", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": null}]}

data: {"id": "chatcmpl-2197de5780854e78b007876f2155e638", "object": "chat.completion.chunk", "created": 1772930038, "model": "Qwen/Qwen3-0.6B", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Python "}, "finish_reason": null}]}

data: {"id": "chatcmpl-2197de5780854e78b007876f2155e638", "object": "chat.completion.chunk", "created": 1772930038, "model": "Qwen/Qwen3-0.6B", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "is "}, "finish_reason": null}]}

data: {"id": "chatcmpl-2197de5780854e78b007876f2155e638", "object": "chat.completion.chunk", "created": 1772930038, "model": "Qwen/Qwen3-0.6B", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "a "}, "finish_reason": null}]}

    ...

data: {"id": "chatcmpl-2197de5780854e78b007876f2155e638", "object": "chat.completion.chunk", "created": 1772930038, "model": "Qwen/Qwen3-0.6B", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 19, "completion_tokens": 54, "total_tokens": 73}}

data: [DONE]

------------------------------------------------------------------------

## 4.4 Context Explorer with Local Server

Configuration used:

OPENAI_API_KEY=dummy OPENAI_API_ENDPOINT=http://localhost:8000/v1
MODEL=qwen3-1.7b

![alt text](context_explorer_server.png)

![alt text](context_explorer_server-1.png)

![alt text](context_explorer_server-2.png)
------------------------------------------------------------------------

## 4.5 Issues Encountered and Fixes

El `devcontainer.json` usa `mcr.microsoft.com/devcontainers/base:ubuntu-22.04`, una imagen base sin soporte CUDA. Esto obligó a correr el modelo en CPU, lo que limitó el uso a Qwen3-0.6B por restricciones de RAM.

------------------------------------------------------------------------

# 5. Conclusions

## 5.1 Understanding LLM Conversations

What you learned about how LLM conversations work:

-   
-   
-   

------------------------------------------------------------------------

## 5.2 Building an OpenAI-Compatible Server

What surprised you about implementing the API:

-   
-   
-   

------------------------------------------------------------------------

## 5.3 Reflection on Vibe Coding

What worked well:

-   

What did not work well:

-   

What you would do differently next time:

-   

------------------------------------------------------------------------

# Appendix

## A. Project Setup

Dependencies:

uv add -r requirements.txt

Install commands:

uv init uv add fastapi uvicorn transformers torch

Run server:

uv run uvicorn main:app --reload

------------------------------------------------------------------------

## B. Key Files

project-root/

├── main.py ├── model_loader.py ├── streaming.py ├── requirements.txt
└── README.md