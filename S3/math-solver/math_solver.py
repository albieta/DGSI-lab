import json
import os
import re
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sympy import Eq, factor, lambdify, simplify, solve, symbols
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


matplotlib.use("Agg")
import matplotlib.pyplot as plt

load_dotenv()

console = Console()
client = None

MODEL = os.getenv("MODEL", "gpt-4.1-mini")
OPENAI_API_ENDPOINT = os.getenv("OPENAI_API_ENDPOINT")
PLOTS_DIR = Path(__file__).resolve().parent / "plots"
X_SYMBOL = symbols("x")
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
ALLOWED_WORD_TOKENS = {
    "x",
    "y",
    "sin",
    "cos",
    "tan",
    "sqrt",
    "log",
    "ln",
    "exp",
    "pi",
    "e",
}

SYSTEM_PROMPT = """
You are a helpful educational math tutor for secondary-school students.

Your goals:
- Explain math clearly and step by step.
- Be concise, friendly, and accurate.
- Use tools for arithmetic, algebra, solving, factoring, quadratic analysis, and plotting.
- Do not guess calculations when a tool should be used.
- Only answer without tools for very small conversational text such as greetings or thanks.

Tool usage rules:
- Use evaluate_expression for arithmetic or symbolic evaluation.
- Use solve_equation for equations such as 2x + 5 = 17.
- Use factor_expression for factoring requests.
- Use analyze_quadratic for vertex, roots, and axis of symmetry questions.
- Use plot_function when the user asks for a graph or when a graph is clearly useful for a quadratic graph question.

After you receive tool results, give a clear final explanation in student-friendly language.
If a tool reports an error, explain the issue clearly and suggest how the student could rephrase the problem.
"""

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "evaluate_expression",
            "description": "Evaluate an arithmetic or algebraic expression safely with SymPy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expression to evaluate, for example (3/4 + 2/3) * 6",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_equation",
            "description": "Solve a one-variable equation such as 2x + 5 = 17 or x^2 - 5x + 6 = 0.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equation": {
                        "type": "string",
                        "description": "Equation to solve, including the equals sign.",
                    }
                },
                "required": ["equation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "factor_expression",
            "description": "Factor an algebraic expression such as x^2 + 7x + 12.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expression to factor.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_quadratic",
            "description": "Analyze a quadratic expression and return vertex, axis of symmetry, and roots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Quadratic expression such as y = x^2 - 6x + 5 or x^2 - 6x + 5.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plot_function",
            "description": "Create a PNG plot of a function over a chosen x-range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Function expression such as y = x^2 - 4x + 3.",
                    },
                    "x_min": {
                        "type": "number",
                        "description": "Minimum x-value for the plot.",
                    },
                    "x_max": {
                        "type": "number",
                        "description": "Maximum x-value for the plot.",
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Optional custom file name. If omitted, a unique name is generated.",
                    },
                },
                "required": ["expression", "x_min", "x_max"],
            },
        },
    },
]


def normalize_math_text(text: str) -> str:
    return text.strip().replace("^", "**")


def strip_left_hand_side(expression: str) -> str:
    cleaned = normalize_math_text(expression)
    if "=" in cleaned:
        left, right = [part.strip() for part in cleaned.split("=", 1)]
        if left.lower() == "y":
            return right
    return cleaned


def validate_expression_text(expression: str) -> None:
    tokens = re.findall(r"[A-Za-z_]+", expression)
    invalid_tokens = sorted({token for token in tokens if token.lower() not in ALLOWED_WORD_TOKENS})
    if invalid_tokens:
        token_list = ", ".join(invalid_tokens)
        raise ValueError(
            f"Unsupported text in expression: {token_list}. Please use a math expression involving x."
        )


def parse_math_expression(expression: str):
    cleaned = strip_left_hand_side(expression)
    validate_expression_text(cleaned)
    parsed = parse_expr(cleaned, transformations=TRANSFORMATIONS, local_dict={"x": X_SYMBOL})
    if not isinstance(parsed, Expr):
        raise ValueError("The input is not a valid mathematical expression.")
    return parsed


def parse_equation(equation: str):
    cleaned = normalize_math_text(equation)
    if "=" not in cleaned:
        raise ValueError("The equation must include '='.")
    left_text, right_text = [part.strip() for part in cleaned.split("=", 1)]
    left_expr = parse_expr(left_text, transformations=TRANSFORMATIONS, local_dict={"x": X_SYMBOL})
    right_expr = parse_expr(right_text, transformations=TRANSFORMATIONS, local_dict={"x": X_SYMBOL})
    return Eq(left_expr, right_expr)


def format_sympy_value(value) -> str:
    exact_text = str(simplify(value))
    try:
        numeric = float(value.evalf())
    except (TypeError, ValueError):
        return exact_text
    rounded = f"{numeric:.6f}".rstrip("0").rstrip(".")
    if rounded == exact_text:
        return exact_text
    return f"{exact_text} (approx. {rounded})"


def ensure_plots_dir() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def build_plot_filename(expression: str) -> str:
    base_name = "quadratic_plot" if "**2" in normalize_math_text(expression) else "function_plot"
    return f"{base_name}_{uuid4().hex[:8]}.png"


def evaluate_expression(expression: str) -> str:
    try:
        expr = parse_math_expression(expression)
        exact_value = simplify(expr)
        response_lines = [f"Expression: {expression}", f"Exact result: {exact_value}"]
        if exact_value.is_number:
            response_lines.append(f"Decimal approximation: {format_sympy_value(exact_value)}")
        return "\n".join(response_lines)
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: I could not evaluate that expression. Details: {exc}"


def solve_equation(equation: str) -> str:
    try:
        eq = parse_equation(equation)
        solutions = solve(eq, X_SYMBOL)
        if not solutions:
            return f"Equation: {equation}\nNo real or symbolic solutions were found."
        formatted_solutions = ", ".join(format_sympy_value(solution) for solution in solutions)
        return (
            f"Equation: {equation}\n"
            f"Simplified form: {simplify(eq.lhs - eq.rhs)} = 0\n"
            f"Solution(s) for x: {formatted_solutions}"
        )
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: I could not solve that equation. Details: {exc}"


def factor_expression(expression: str) -> str:
    try:
        expr = parse_math_expression(expression)
        factored = factor(expr)
        return f"Expression: {expression}\nFactored form: {factored}"
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: I could not factor that expression. Details: {exc}"


def analyze_quadratic(expression: str) -> str:
    try:
        expr = simplify(parse_math_expression(expression))
        polynomial = expr.expand()
        a = polynomial.coeff(X_SYMBOL, 2)
        b = polynomial.coeff(X_SYMBOL, 1)
        c = polynomial.coeff(X_SYMBOL, 0)

        if a == 0:
            return "Error: That is not a quadratic expression in x."

        vertex_x = -b / (2 * a)
        vertex_y = simplify(expr.subs(X_SYMBOL, vertex_x))
        roots = solve(Eq(expr, 0), X_SYMBOL)
        roots_text = ", ".join(format_sympy_value(root) for root in roots) if roots else "No real or symbolic roots found"

        return "\n".join(
            [
                f"Quadratic: {expression}",
                f"Standard form: {polynomial}",
                f"Vertex: ({format_sympy_value(vertex_x)}, {format_sympy_value(vertex_y)})",
                f"Axis of symmetry: x = {format_sympy_value(vertex_x)}",
                f"Roots: {roots_text}",
            ]
        )
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: I could not analyze that quadratic. Details: {exc}"


def plot_function(
    expression: str,
    x_min: float,
    x_max: float,
    output_file: str | None = None,
) -> str:
    try:
        if x_min >= x_max:
            return "Error: x_min must be smaller than x_max."

        expr = simplify(parse_math_expression(expression))
        unknown_symbols = sorted(str(symbol) for symbol in expr.free_symbols if symbol != X_SYMBOL)
        if unknown_symbols:
            symbol_list = ", ".join(unknown_symbols)
            return (
                "Error: I can only plot expressions in x. "
                f"I found unsupported symbol(s): {symbol_list}."
            )
        if X_SYMBOL not in expr.free_symbols and not expr.is_number:
            return "Error: I could not interpret that as a plottable function of x."

        func = lambdify(X_SYMBOL, expr, modules=["numpy"])
        x_values = np.linspace(x_min, x_max, 400)
        y_values = np.array(func(x_values), dtype=float)
        if y_values.ndim == 0:
            y_values = np.full_like(x_values, float(y_values))
        if not np.all(np.isfinite(y_values)):
            return "Error: The function produced non-finite values in that x-range."

        ensure_plots_dir()
        file_name = output_file if output_file else build_plot_filename(expression)
        file_path = PLOTS_DIR / Path(file_name).name

        plt.figure(figsize=(8, 5))
        plt.plot(x_values, y_values, label=f"y = {expr}", color="navy")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.axvline(0, color="black", linewidth=0.8)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Function Plot")

        if expr.expand().coeff(X_SYMBOL, 2) != 0:
            a = expr.expand().coeff(X_SYMBOL, 2)
            b = expr.expand().coeff(X_SYMBOL, 1)
            vertex_x = float((-b / (2 * a)).evalf())
            vertex_y = float(expr.subs(X_SYMBOL, vertex_x).evalf())
            if x_min <= vertex_x <= x_max:
                plt.scatter([vertex_x], [vertex_y], color="crimson", zorder=5, label="Vertex")

        plt.legend()
        plt.tight_layout()
        plt.savefig(file_path, dpi=150)
        plt.close()

        return f"Plot saved to: {file_path}\nExpression plotted: y = {expr}\nRange: x from {x_min} to {x_max}"
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: I could not create that plot. Details: {exc}"


def get_tool_registry() -> dict:
    return {
        "evaluate_expression": evaluate_expression,
        "solve_equation": solve_equation,
        "factor_expression": factor_expression,
        "analyze_quadratic": analyze_quadratic,
        "plot_function": plot_function,
    }


def initialize_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Create a .env file with your API settings."
        )

    if OPENAI_API_ENDPOINT:
        return OpenAI(api_key=api_key, base_url=OPENAI_API_ENDPOINT)
    return OpenAI(api_key=api_key)


def print_configuration() -> None:
    endpoint = OPENAI_API_ENDPOINT or "https://api.openai.com/v1"
    console.print(
        Panel(
            f"Model: {MODEL}\nEndpoint: {endpoint}",
            title="Configuration",
            border_style="cyan",
        )
    )


def print_available_tools() -> None:
    table = Table(title="Tools", border_style="magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Purpose", style="white")
    table.add_row("evaluate_expression", "Evaluate arithmetic or symbolic expressions")
    table.add_row("solve_equation", "Solve one-variable equations")
    table.add_row("factor_expression", "Factor algebraic expressions")
    table.add_row("analyze_quadratic", "Find vertex, axis of symmetry, and roots")
    table.add_row("plot_function", "Save a graph to plots/")
    console.print(table)


def build_initial_messages(user_problem: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_problem},
    ]


def print_tool_call(name: str, arguments: dict) -> None:
    pretty_args = json.dumps(arguments, indent=2, ensure_ascii=False)
    console.print(
        Panel(
            f"{name}\n{pretty_args}",
            title="Tool Call",
            border_style="yellow",
        )
    )


def print_tool_result(name: str, result: str) -> None:
    console.print(
        Panel(
            result,
            title=f"Tool Result: {name}",
            border_style="green",
        )
    )


def execute_tool_call(tool_call, tool_registry: dict) -> dict:
    function_name = tool_call.function.name
    raw_arguments = tool_call.function.arguments or "{}"

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        result = f"Error: invalid tool arguments for {function_name}. Details: {exc}"
        print_tool_result(function_name, result)
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": result,
        }

    print_tool_call(function_name, arguments)

    tool_function = tool_registry.get(function_name)
    if tool_function is None:
        result = f"Error: unknown tool '{function_name}'."
    else:
        try:
            result = tool_function(**arguments)
        except TypeError as exc:
            result = f"Error: invalid arguments for {function_name}. Details: {exc}"
        except Exception as exc:  # pragma: no cover - defensive fallback for CLI reliability
            result = f"Error: unexpected tool failure in {function_name}. Details: {exc}"

    print_tool_result(function_name, result)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": function_name,
        "content": result,
    }


def request_completion(messages: list[dict]):
    return client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=AVAILABLE_TOOLS,
        temperature=0.2,
    )


def append_assistant_tool_call_message(messages: list[dict], assistant_message) -> None:
    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in assistant_message.tool_calls
            ],
        }
    )


def solve_with_tools(user_problem: str) -> str:
    messages = build_initial_messages(user_problem)
    tool_registry = get_tool_registry()

    for _ in range(6):
        response = request_completion(messages)
        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            append_assistant_tool_call_message(messages, assistant_message)
            for tool_call in assistant_message.tool_calls:
                tool_message = execute_tool_call(tool_call, tool_registry)
                messages.append(tool_message)
            continue

        final_answer = assistant_message.content or "I could not produce a final answer."
        messages.append({"role": "assistant", "content": final_answer})
        return final_answer

    return "I could not finish the tool-calling loop cleanly. Please try rephrasing the problem."


def ask_yes_no(prompt_text: str) -> bool:
    answer = console.input(f"{prompt_text} ").strip().lower()
    return answer in {"y", "yes"}


def run_cli() -> None:
    while True:
        console.print()
        user_problem = console.input("[bold cyan]Enter a math problem:[/bold cyan] ").strip()

        if not user_problem:
            console.print(
                Panel(
                    "Please enter a math problem or press Ctrl+C to exit.",
                    border_style="yellow",
                )
            )
            continue

        try:
            final_answer = solve_with_tools(user_problem)
            console.print()
            console.print(
                Panel(
                    final_answer,
                    title="Final Explanation",
                    border_style="blue",
                )
            )
        except Exception as exc:  # pragma: no cover - CLI safety net
            console.print(
                Panel(
                    f"Something went wrong while solving the problem.\nDetails: {exc}",
                    title="Error",
                    border_style="red",
                )
            )

        if not ask_yes_no("[bold magenta]Solve another problem? (y/n)[/bold magenta]"):
            break


def main() -> None:
    global client

    try:
        client = initialize_client()
    except RuntimeError as exc:
        console.print(Panel(str(exc), title="Configuration Error", border_style="red"))
        return

    print_configuration()
    print_available_tools()
    run_cli()


if __name__ == "__main__":
    main()
