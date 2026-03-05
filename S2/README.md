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

-   
-   
-   
-   

Example messages array snapshot:

Paste example here

## 1.3 Token Usage Growth

Describe how token usage changes across turns.

Observations:

-   prompt_tokens growth:
-   completion_tokens growth:
-   total_tokens behavior:

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

Explain in your own words:

-   What the messages array is
-   Why the full conversation history is sent on every request

Explanation:

-   

Example structure:

{ "messages": \[ {"role": "system", "content": "..."}, {"role": "user",
"content": "..."}, {"role": "assistant", "content": "..."} \] }

## 2.2 Streaming vs Non-Streaming Responses

Explain the difference between streaming and non-streaming responses.

Non-streaming:

-   

Streaming:

-   

Comparison:

  Feature         Non-streaming   Streaming
  --------------- --------------- -----------
  Response type                   
  Latency                         
  Use cases                       

Example non-streaming response:

Paste response example

Example streaming chunks:

data: {...} data: {...} data: \[DONE\]

## 2.3 What is Server-Sent Events (SSE)?

Explain SSE and how it is used in LLM APIs.

Explanation:

-   

How SSE works:

-   

Example SSE format:

data: {...}

data: {...}

data: \[DONE\]

## 2.4 Why the OpenAI API Became a Standard

Explain why the OpenAI API format became the de facto standard.

Discussion points:

-   
-   
-   

------------------------------------------------------------------------

# 3. FastAPI Server --- Design and Implementation

## 3.1 Server Architecture

Describe the overall architecture of your server.

Components:

-   FastAPI server
-   Model loading
-   Chat completions endpoint
-   Streaming logic

Architecture description:

-   

Optional diagram:

Insert architecture diagram if needed

------------------------------------------------------------------------

## 3.2 Model Loading

Explain how the Qwen3 model and tokenizer are loaded.

Code snippet:

Paste model loading code

Explanation:

-   
-   

------------------------------------------------------------------------

## 3.3 /v1/models Endpoint

Describe the endpoint that returns the available models.

Example response:

{ "object": "list", "data": \[ { "id": "qwen3-1.7b", "object": "model" }
\] }

Implementation snippet:

Paste code

Explanation:

-   

------------------------------------------------------------------------

## 3.4 /v1/chat/completions Endpoint (Non-Streaming)

Describe how the non-streaming completion works.

Request structure:

Paste request example

Response structure:

Paste response example

Implementation snippet:

Paste code

Explanation:

-   

------------------------------------------------------------------------

## 3.5 Streaming Implementation

Explain how streaming responses are implemented.

Key components:

-   StreamingResponse
-   TextIteratorStreamer
-   SSE formatting

Code snippet:

Paste streaming code

Example stream output:

data: {...}

data: {...}

data: \[DONE\]

Explanation:

-   

------------------------------------------------------------------------

## 3.6 Token Counting

Explain how prompt and completion tokens are counted.

Code snippet:

Paste token counting logic

Explanation:

-   

------------------------------------------------------------------------

## 3.7 AI Collaboration Log (Vibe Coding Process)

Describe how you used AI tools during development.

AI tools used:

-   
-   
-   

Example prompts you used:

Paste prompts here

What the AI got right:

-   

What the AI got wrong:

-   

How you fixed issues:

-   

------------------------------------------------------------------------

# 4. Testing Evidence

## 4.1 Testing /v1/models

Command:

curl http://localhost:8000/v1/models

Output:

Paste output

------------------------------------------------------------------------

## 4.2 Non-Streaming Completion Test

Command:

curl http://localhost:8000/v1/chat/completions\
-H "Content-Type: application/json"\
-d '{ "model": "qwen3-1.7b", "messages": \[ {"role": "user", "content":
"What is FastAPI?"} \] }'

Output:

Paste output

------------------------------------------------------------------------

## 4.3 Streaming Completion Test

Command:

curl http://localhost:8000/v1/chat/completions\
-H "Content-Type: application/json"\
-N\
-d '{ "model": "qwen3-1.7b", "messages": \[ {"role": "user", "content":
"Explain Python."} \], "stream": true }'

Output:

Paste streaming output

------------------------------------------------------------------------

## 4.4 Context Explorer with Local Server

Configuration used:

OPENAI_API_KEY=dummy OPENAI_API_ENDPOINT=http://localhost:8000/v1
MODEL=qwen3-1.7b

Conversation transcript or screenshot:

Paste conversation

Verification:

-   Multi-turn conversation works
-   Messages array grows correctly
-   Streaming works

------------------------------------------------------------------------

## 4.5 Issues Encountered and Fixes

Issue 1:

Problem:

Solution:

Issue 2:

Problem:

Solution:

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

fastapi uvicorn transformers torch

Install commands:

uv init uv add fastapi uvicorn transformers torch

Run server:

uv run uvicorn main:app --reload

------------------------------------------------------------------------

## B. Key Files

project-root/

├── main.py ├── model_loader.py ├── streaming.py ├── requirements.txt
└── README.md