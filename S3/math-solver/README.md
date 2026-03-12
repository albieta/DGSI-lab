## Math Solver CLI

Educational command-line math solver using OpenAI tool calling plus Python math tools.

### `.env`

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_ENDPOINT=https://api.openai.com/v1
MODEL=gpt-4.1-mini
```

`OPENAI_API_ENDPOINT` is optional. Leave it out if you want the default OpenAI endpoint.

### Install

```bash
uv sync
```

Or:

```bash
uv add openai python-dotenv sympy matplotlib numpy rich
```

### Run

```bash
python3 math_solver.py
```

You can also run:

```bash
python3 main.py
```

### Tool-calling flow

1. The user enters a math problem in natural language.
2. The model decides which math tool to call.
3. Python executes the tool with SymPy or matplotlib.
4. Tool results are sent back to the model.
5. The model returns a student-friendly final explanation.
