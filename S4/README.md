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
```

### Code

```python
```

### Output / Proof

<!-- Screenshot or terminal output showing the table was created. -->

---

## Step 2: The Loop — Multiple Tool Calls in Sequence

### Loop Code

```python
```

### Terminal Output

<!-- Show both tool calls (CREATE TABLE and INSERT) visible in the output. -->

### Stop Condition

<!-- Explain how the program knows when to stop looping. -->

---

## Step 3: The wget Tool with User Confirmation

### wget Tool Schema

```json
```

### Confirmation Code

```python
```

### Output — User Approves

<!-- Terminal output when the user types y. -->

### Output — User Denies

<!-- Terminal output when the user does not approve. -->

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