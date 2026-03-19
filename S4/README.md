# Week 4 — Function Calling in Practice: From One Call to Many

## Step 0: Research

### SQLite

<!-- Explain what SQLite is, how it differs from server-based databases like PostgreSQL or MySQL,
     where tables and indexes are stored, and what happens with concurrent writes. -->

### subprocess.run()

<!-- Explain how subprocess.run() works, what capture_output=True, text=True, and timeout do,
     whether it is synchronous or asynchronous, and when you would use subprocess.Popen() instead. -->

### wget

<!-- Explain what wget does, what the -q and -O - flags mean, and what happens when the URL
     does not exist or the server is slow. -->

---

## Step 1: Project Setup and a Single Tool Call

### Tool Schema

```json
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
```

### Code

```python
def execute_sql(statement: str) -> str:
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(statement)
        connection.commit()

        if cursor.description:
            rows = cursor.fetchall()
            return json.dumps(rows)

    return f"SQL executed successfully: {statement}"
```

### Output / Proof

![](./media/1.png)

---

## Step 2: The Loop — Multiple Tool Calls in Sequence

### Loop Code

```python
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
```

### Terminal Output

![](./media/2.png)

### Stop Condition

<!-- Explain how the program knows when to stop looping. -->

---

## Step 3: The wget Tool with User Confirmation

### wget Tool Schema

```json
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
```

### Confirmation Code

```python
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
```

### Output — User Approves

![](./media/3.png)

### Output — User Denies

![](./media/4.png)

---

## Step 4: The Full Test — Fetch, Store, Query

### Full Terminal Output

<!-- Complete output of the run with the test prompt. -->

### Independent SQLite Verification

```
sqlite3 database.db "SELECT * FROM users;"
```

<!-- Paste the output here. -->

### Number of Loop Iterations

<!-- How many iterations did the loop run? Were you surprised? -->

---

## Step 5: Polish and Error Handling

### Error Case 1 — Bad URL

<!-- Show the terminal output and how the program handled it without crashing. -->

### Error Case 2 — Invalid SQL

<!-- Show the terminal output and how the program handled it without crashing. -->

---

## Required Questions

1. How does your program know when to stop calling the LLM?

2. What is the role of `tool_call_id` in the message protocol?

3. Why is user confirmation important for the wget tool but not for `execute_sql`?

4. What happens in the conversation when the user denies a wget command?

5. How many iterations did the loop run for the full test prompt? Were you surprised?

---

## Extra Challenge: Does the Model Matter? *(optional)*

<!-- Compare results between qwen3.5-122b-a10b and qwen2.5-vl-72b-instruct.
     Which model worked better? Where did the smaller model struggle? -->

---

## GitHub Repository

<!-- Link to your repository here. -->