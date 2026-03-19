import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
PROMPT = "Create a table called test with columns: id INTEGER, name TEXT."


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
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(statement)
        connection.commit()

        if cursor.description:
            rows = cursor.fetchall()
            return json.dumps(rows)

    return f"SQL executed successfully: {statement}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Run a SQL statement against the local SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "statement": {
                        "type": "string",
                        "description": "The SQL statement to execute.",
                    }
                },
                "required": ["statement"],
                "additionalProperties": False,
            },
        },
    }
]


def main() -> None:
    client, model = load_config()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a careful database assistant. Use the provided SQL tool for database changes.",
            },
            {"role": "user", "content": PROMPT},
        ],
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if not message.tool_calls:
        print("Model did not return a tool call.")
        print("Assistant response:", message.content)
        return

    print("Tool call received:")
    for tool_call in message.tool_calls:
        print(json.dumps(tool_call.model_dump(), indent=2))

        arguments = json.loads(tool_call.function.arguments)
        result = execute_sql(arguments["statement"])
        print("\nExecution result:")
        print(result)


if __name__ == "__main__":
    main()
