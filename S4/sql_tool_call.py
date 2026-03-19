import json
import os
import shlex
import sqlite3
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
PROMPT = "Download the content from https://jsonplaceholder.typicode.com/users"
SYSTEM_PROMPT = (
    "You are a careful assistant that can use SQL and wget tools. "
    "Use execute_sql for database work. "
    "Use wget when the user asks to download content from a URL. "
    "Do not combine CREATE and INSERT into a single tool call."
    "If a task needs multiple tool calls, do them one at a time in sequence. "
    "After tool work is finished, provide a short final answer."
)


def load_config() -> tuple[OpenAI, str]:
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to S4/.env before running.")

    base_url = os.getenv("OPENAI_API_ENDPOINT")
    model = os.getenv("MODEL", "gpt-4.1-mini")

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def execute_sql(statement: str) -> str:
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(statement)
            connection.commit()

            if cursor.description:
                rows = cursor.fetchall()
                return json.dumps(rows)
    except sqlite3.Error as error:
        return f"SQLite error: {error}"

    return f"SQL executed successfully: {statement}"


def run_wget(url: str) -> str:
    command = ["wget", "-qO-", url]
    command_text = shlex.join(command)

    print("\nProposed wget command:")
    print(command_text)
    approval = input("Approve this command? [y/N]: ").strip().lower()

    if approval != "y":
        return f"User denied command: {command_text}"

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        return f"Failed to run wget: {error}"

    if result.returncode != 0:
        error_text = result.stderr.strip() or "wget returned a non-zero exit code."
        return f"wget failed: {error_text}"

    return result.stdout.strip()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Run one SQL statement against the local SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "statement": {
                        "type": "string",
                        "description": "A single SQL statement to execute.",
                    }
                },
                "required": ["statement"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wget",
            "description": "Download the contents of a URL using the local wget command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to download.",
                    }
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    }
]


def execute_tool(tool_name: str, arguments: dict[str, str]) -> str:
    if tool_name == "execute_sql":
        return execute_sql(arguments["statement"])

    if tool_name == "wget":
        return run_wget(arguments["url"])

    return f"Unknown tool: {tool_name}"


def run_conversation_loop(client: OpenAI, model: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": PROMPT},
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "Model returned no final text."

        for index, tool_call in enumerate(message.tool_calls, start=1):
            print(f"\nTool call {index}:")
            print(json.dumps(tool_call.model_dump(), indent=2))

            arguments = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_call.function.name, arguments)

            print("Execution result:")
            print(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )


def main() -> None:
    client, model = load_config()

    final_answer = run_conversation_loop(client, model)
    print("\nFinal answer:")
    print(final_answer)


if __name__ == "__main__":
    main()
