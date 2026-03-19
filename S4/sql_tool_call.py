import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
PROMPT = (
    "Create a table called cities with columns id and name. "
    "Then insert three Spanish cities."
)
SYSTEM_PROMPT = (
    "You are a careful database assistant. "
    "Always use the provided SQL tool for database changes. "
    "If a task needs multiple SQL statements, call the tool once per statement in sequence. "
    "Do not combine CREATE and INSERT into a single tool call. "
    "After the tool work is done, give a short final summary."
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


def reset_demo_table() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DROP TABLE IF EXISTS cities")
        connection.commit()


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
    }
]


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
            result = execute_sql(arguments["statement"])

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
    reset_demo_table()

    final_answer = run_conversation_loop(client, model)
    print("\nFinal answer:")
    print(final_answer)


if __name__ == "__main__":
    main()
