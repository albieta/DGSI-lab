# Week 4 — Function Calling in Practice: From One Call to Many

## Step 0: Research

### SQLite
**Explain what SQLite is, how it differs from server-based databases like PostgreSQL or MySQL, where tables and indexes are stored, and what happens with concurrent writes.**

SQLite no és un servidor de base de dades, com MySQL o PostgreSQL, sinó que és una llibreria que guarda tota la base de dades en un sol fitxer. Quan executem sqlite3 test.db, el que fem és crear un fitxer que conté les taules, índexs i dades en un mateix lloc.

Això representa una diferència substancial a PostgreSQL o MySQL, ja que en aquests casos hi ha un servidor per darrere. Aquest s'encarrega de gestionar connexions concurrents, de manera que podem tenir múltiples clients accedint a la base de dades al mateix temps. 

Les taules i els índexs estan tots dins del fitxer .db creat a partir d ela comanda especificada a l'enunciat. Si fem un 'ls', veurem el nostre fitxer test.db representat com a un fitxer normal al sistema de fitxers. No hi ha cap directori, cap procés extra de fons, ni cap configuració a tenir en compte.

El principal problema que trobem en SQLite és el de la concurrència d'escriptures. Si dos programes intenten escriure al mateix fitxer alhora, SQLite ho gestiona fent un bloqueig del fitxer (file locking). Així doncs, només el primer programa hi podrà escriure. El segon, s'haurà d'esperar (SQLITE_BUSY). Per a aquest lab no és important, perquè només hi ha un procés accedint a la base de dades. Precisament, SQLite és una molt bona opció per a entorns locals i fer tot tipus de proves. En canvi, en una aplicació web amb milers d'usuaris simultanis, SQLite ens acabaria generant un coll d'ampolla gegant, causant molts problemes.

Altres coses que PostgreSQL pot fer i SQLite no és gestionar moltes connexions concurrents, integrar un sistema de permisos i usuaris, funcionar en xarxa, i escala a bases de dades de centenars de gigabytes. Això, no obstant, no és un problema de disseny, sinó que és una elecció a consciència. SQLite ha estat dissenyat per a ser senzill, lleuger i fàcil d'utilitzar i està pensat per casos d'ús i entorns diferents als de PostgreSQL o MySQL.

### subprocess.run()

**Explain how subprocess.run() works, what capture_output=True, text=True, and timeout do, whether it is synchronous or asynchronous, and when you would use subprocess.Popen() instead.**

### wget

**Explain what wget does, what the -q and -O - flags mean, and what happens when the URL does not exist or the server is slow.**

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
```

### Terminal Output

** Show both tool calls (CREATE TABLE and INSERT) visible in the output. **

### Stop Condition

** Explain how the program knows when to stop looping. **

---

## Step 3: The wget Tool with User Confirmation

### wget Tool Schema

```json
```

### Confirmation Code

```python
```

### Output — User Approves

** Terminal output when the user types y. **

### Output — User Denies

** Terminal output when the user does not approve. **

---

## Step 4: The Full Test — Fetch, Store, Query

### Full Terminal Output

** Complete output of the run with the test prompt. **

### Independent SQLite Verification

```
sqlite3 database.db "SELECT * FROM users;"
```

** Paste the output here. **

### Number of Loop Iterations

** How many iterations did the loop run? Were you surprised? **

---

## Step 5: Polish and Error Handling

### Error Case 1 — Bad URL

** Show the terminal output and how the program handled it without crashing. **

### Error Case 2 — Invalid SQL

** Show the terminal output and how the program handled it without crashing. **

---

## Required Questions

1. How does your program know when to stop calling the LLM?

2. What is the role of `tool_call_id` in the message protocol?

3. Why is user confirmation important for the wget tool but not for `execute_sql`?

4. What happens in the conversation when the user denies a wget command?

5. How many iterations did the loop run for the full test prompt? Were you surprised?

---

## Extra Challenge: Does the Model Matter? *(optional)*

** Compare results between qwen3.5-122b-a10b and qwen2.5-vl-72b-instruct. Which model worked better? Where did the smaller model struggle? **

---

## GitHub Repository
[https://github.com/albieta/DGSI-lab](https://github.com/albieta/DGSI-lab)