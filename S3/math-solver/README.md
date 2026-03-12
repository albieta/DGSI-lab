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


PROMPT

```text
Build a complete Python CLI application called `math_solver.py` that follows the same API credential and endpoint pattern as my existing Three Little Pigs function-calling demo, but for a different use case: a small educational math problem solver for secondary-school students.

I want clean, understandable, well-structured code split into multiple functions instead of one huge script.

Context and constraints:
- Use Python.
- Use the OpenAI-compatible Python client from `openai`.
- Load configuration from a local `.env` using `python-dotenv`.
- Reuse the same credential pattern as my current demo:
  - `OPENAI_API_KEY`
  - `OPENAI_API_ENDPOINT` (optional custom base URL)
  - `MODEL` with default fallback like `gpt-4.1-mini`
- The app should accept a math problem from the user in natural language.
- It must use LLM function calling / tools.
- The model must not guess calculations when a tool should be used.
- Real math work must be performed in Python tools.
- It must be able to generate at least one `.png` plot when appropriate.
- It must return a clear final explanation for the user.
- It should handle some invalid input gracefully without crashing.

Supported example requests:
- “Solve 2x + 5 = 17.”
- “What are the roots of x^2 - 5x + 6 = 0?”
- “Evaluate (3/4 + 2/3) * 6.”
- “Factor x^2 + 7x + 12.”
- “Plot y = x^2 - 4x + 3 from x = -2 to x = 6.”
- “What is the vertex of y = x^2 - 6x + 5? Plot it too.”

Requirements:
1. Read API key, endpoint, and model from `.env`
2. Use the same client initialization pattern as my demo
3. Accept a user math problem in natural language from the terminal
4. Provide at least 4 math tools via function calling
5. Execute chosen tools in Python
6. Return a final answer in clear student-friendly language
7. Generate `.png` plots for graphing requests
8. Handle invalid input without crashing
9. Separate logic into multiple functions
10. Show tool calls in the terminal so it is easy to follow
11. Save plots into a `plots/` folder with meaningful unique filenames

Use these libraries:
- `openai`
- `python-dotenv`
- `sympy`
- `matplotlib`
- `pathlib`
- `uuid`

You may also use:
- `numpy`
- `rich`

Please implement the app with a structure like this inside one file unless a second helper file is truly necessary:
- configuration loading
- OpenAI client initialization
- tool schema definitions
- Python implementations of the tools
- chat / reasoning loop with function calling
- CLI entry point

Design rules:
- Keep the tool set small and clear.
- Do not create one mega-function like `do_math_everything()`.
- Each tool should do one job well.
- Prefer clarity over cleverness.
- The code should be understandable by a student reviewing it.

Implement at least these tools:
1. `evaluate_expression(expression: str) -> str`
   - Evaluate arithmetic expressions safely with SymPy
   - Return exact form when possible and numeric approximation when useful

2. `solve_equation(equation: str) -> str`
   - Solve one-variable equations like `2x + 5 = 17` or `x^2 - 5x + 6 = 0`
   - Use SymPy
   - Return solutions clearly

3. `factor_expression(expression: str) -> str`
   - Factor algebraic expressions like `x^2 + 7x + 12`
   - Use SymPy

4. `analyze_quadratic(expression: str) -> str`
   - For expressions like `y = x^2 - 6x + 5` or `x^2 - 6x + 5`
   - Return vertex, axis of symmetry, and roots if available

5. `plot_function(expression: str, x_min: float, x_max: float, output_file: str | None = None) -> str`
   - Generate a `.png` plot using matplotlib
   - Save it to `plots/`
   - Support expressions like `y = x^2 - 4x + 3`
   - Return the saved file path and a short description

Important behavior for the LLM system prompt:
- The assistant is a helpful educational math tutor for high-school students.
- It should explain clearly and step by step.
- It must use tools for arithmetic, algebra, solving, factoring, and plotting instead of guessing.
- It should only answer directly without tools for very minor conversational text.
- If plotting is requested or useful for a quadratic graph question, it should call the plotting tool.
- After tool results are returned, it should give a concise, student-friendly final explanation.

Implementation details:
- Use OpenAI chat completions with `tools=[...]`.
- Detect and execute tool calls in a loop until the model returns a normal final answer.
- Print tool calls and tool results in the terminal.
- Include a clean `SYSTEM_PROMPT`.
- Include robust parsing helpers for math text:
  - Convert `^` to `**`
  - Handle implicit `y = ...` when plotting
  - Handle equations with `=`
  - Use SymPy parsing carefully
- Use `sympy.sympify`, `symbols`, `Eq`, `solve`, `factor`, and related utilities where appropriate.
- For plotting:
  - Use numpy sampling over the given x-range
  - Use matplotlib to save a `.png`
  - Mark the vertex on the graph when the expression is quadratic, if easy to do
- Validate x range for plotting and return a readable error if invalid.
- Create `plots/` automatically if it does not exist.
- Use meaningful plot filenames, e.g. `quadratic_plot_<short_uuid>.png`

User experience:
- Start with a simple terminal prompt like: `Enter a math problem:`
- Run one query, solve it, and print the final explanation.
- After that, optionally ask whether the user wants to solve another problem.
- Keep the CLI simple and reliable.

Output format:
- Return the full code for the application.
- Also include a sample `.env` block.
- Also include a short `requirements.txt` or `uv add ...` line.
- Also include a brief explanation of how the tool-calling flow works in this code.

Please model the coding style after my existing demo:
- readable sections
- clear comments
- configuration near the top
- multiple helper functions
- terminal-friendly output
- straightforward control flow

But adapt it fully to the math-solver use case rather than the Three Little Pigs story.
```