## Math Solver CLI

Educational command-line math solver using OpenAI tool calling plus Python math tools.

### `.env`

```env
OPENAI_API_KEY=...
OPENAI_API_ENDPOINT=...
MODEL=...
```

`OPENAI_API_ENDPOINT` is optional. Leave it out if you want the default OpenAI endpoint.

### Install

```bash
uv sync
```

### Run

```bash
uv run python math_solver.py
```

### Tool-calling flow

1. The user enters a math problem in natural language.
2. The model decides which math tool to call.
3. Python executes the tool with SymPy or matplotlib.
4. Tool results are sent back to the model.
5. The model returns a student-friendly final explanation.
