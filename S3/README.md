# Week 3 Report: Function Calling, Tools, and LLMs That Can Act

## 1. Three Little Pigs Demo Test

**Configuration**
To run the demo, we created a local `.env` file containing the API details from `apikey.md`. The configuration was set up to use the OpenAI-compatible endpoint for Alibaba Cloud:
*   `OPENAI_API_KEY`: *(Not written for security)*
*   `OPENAI_API_ENDPOINT`: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
*   `MODEL`: `qwen3.5-122b-a10b`

**Evidence of Both Scenarios**
*   **Without tools (Scenario 1):** When we ran the no-tool script, we only saw the pig talking and crying but no action was done when threatened.
*   **With tools (Scenario 2):** As shown in the terminal execution, when the wolf escalated the threat by saying *"The door was closed, but the window was open! I have eaten you..."*, the model recognized the danger and used the provided function.
    ```json
    "tool_calls":[
      {
        "id": "call_f7a02b9be3194914824e6523",
        "function": {
          "name": "call_hunter",
          "arguments": "{\"urgency\": \"emergency\", \"message\": \"The Big Bad Wolf is inside my brick house!...\"}"
        }
      }
    ]
    ```
    The application intercepted this, executed `call_hunter()` locally, and returned the output: *"The hunter is sprinting to your location with backup and heavy weapons! Hold on!"*

**What changed when tools were enabled?**
Instead of just responding with natural language about how scared it was, the model's API response structure changed. It returned a structured `tool_calls` JSON array. This paused the conversation, allowing the local Python script to execute an action in the real world (calling the hunter) before sending the result back to the LLM to formulate its final reply.

## 2. Function Calling Explanation

**How function calling works**
Function calling works by sending the LLM a list of available tools (defined as JSON schemas in the OpenAI API standard) alongside the user's prompt. The model reads these descriptions and decides if it needs an external tool to fulfill the user's request. If a tool is needed, the model does not return standard text directly. Instead, it returns a structured JSON object containing the name of the function to call and the specific arguments to pass. The Python script then parses this JSON, executes the real function locally, and sends the output of that function back to the LLM in a second API call. Finally, the LLM uses that real-world output to answer the user.

**The difference between a normal assistant answer and a tool call**
*   **Normal Assistant Answer:** The model responds with a simple text string containing natural language intended directly for the user.
*   **Tool Call:** The model responds with a structured data block (`tool_calls`) meant for the *application* to read. It contains a specific function name and JSON arguments instead of conversational text.

**Why the host program remains in control**
The LLM itself **cannot** execute any code or perform any actions directly. It is only generating text (or JSON). The host Python program remains completely in control because it receives the model's *request* to use a tool, decides whether to allow it, executes the actual code safely on the local machine, and determines what data to send back to the model. The LLM acts only as a decision-maker, while the host program is the executor.

## 3. Math Solver Design

**Description of Chosen Tools**
*   *(Describe the 3-5 tools you built here, e.g., `evaluate_expression`, `solve_equation`, `plot_function`)*

**Why I limited the tool set**
*   *(Explain based on the design rule: Fewer, clearer tools produce better model behavior, prevent the schema from being vague, and stop the model from choosing the wrong tool or getting confused by overlapping functionalities.)*

**Key Code Fragments**
```python
# Insert your favorite snippet here (e.g., your tool definitions or the execution router)
# and briefly explain how it parses the model's request.
```

## 4. Testing Evidence

**Math Problems Tried:**
1.  *(e.g., "Solve 2x + 5 = 17")*
2.  *(e.g., "Factor x^2 + 7x + 12")*
3.  *(e.g., "Plot y = x^2 - 4x + 3")*

**Successful Plot**
*(Insert an image using markdown: `![Plot of Parabola](plots/example.png)`)*

**Failure Case Handling**
*(Describe a time you gave it invalid math syntax or an unsupported prompt, and explain how your `try/except` block caught the error and gracefully informed the model/user without crashing.)*

## 5. Reflection

*   **What did the model do well?** *(e.g., It was great at identifying exactly when to use a math tool vs when to just chat, and it populated the JSON arguments accurately.)*
*   **Where did it choose tools badly or fail?** *(e.g., Sometimes it tried to solve equations using the evaluation tool, or provided badly formatted strings to sympy.)*
*   **What did you learn about using LLMs as orchestrators rather than calculators?** *(e.g., LLMs are brilliant reasoning engines but terrible at deterministic math. By using them as orchestrators, you get the best of both worlds: natural language understanding paired with the 100% accuracy of traditional code.)*

---

## Required Questions

**1. Why is function calling more reliable than asking the model to “just do the math” in plain text?**
LLMs are next-token prediction engines, meaning they essentially guess the most likely next word. They do not have built-in calculators, which makes them highly prone to arithmetic hallucinations. Function calling delegates the actual calculation to deterministic software (like Python functions designed for a certain purpose), ensuring 100% mathematical accuracy.

**2. Why should the available tool set be small and well-defined?**
If there are too many tools or a single "mega-tool," the schema becomes vague. A small, clear toolset minimizes confusion, ensuring the model chooses the correct function (otherwise it might choose the wrong one) and passes the correct arguments without hallucinating parameters.

**3. What is the role of sympy in your solution?**
`sympy` serves as the deterministic mathematical engine. It handles parsing the string expressions passed by the LLM and safely performs symbolic algebra, equation solving, and factoring.

**4. What is the role of matplotlib in your solution?**
`matplotlib` provides a visual artifact for the user. When the LLM recognizes a user wants a graph, it triggers the plotting function, and `matplotlib` translates the mathematical points into a saved `.png` image.

**5. What happens in your program from the moment the user types a problem to the final answer?**
1. User types the prompt.
2. The prompt + tool schemas are sent to the LLM.
3. The LLM returns a `tool_calls` request (e.g., to solve an equation).
4. The Python script intercepts this, parses the arguments, and calls a function that runs the actual `sympy` or `matplotlib` functions.
5. The Python script appends the calculated answer as a `tool` role message and sends it *back* to the LLM.
6. The LLM reads the true answer and generates a final natural-language explanation for the user.

**6. What kinds of errors can still happen even when function calling is used?**
The model might choose the wrong tool for the job, hallucinate arguments that don't match the schema, or pass math syntax that `sympy` fails to parse. The host program must handle these gracefully.

Something we have thaught about is the fact that if the called tool does not provide intermediate steps, the model could be inventing its own steps to reach the final answer, which could lead to hallucinations. This is why an advanced implementation of the tool has to return not just the final answer, but also the intermediate steps, so that the model can use those as a basis for its final explanation to the user.

**7. When should the model answer directly, and when should it call a tool?**
It should answer directly when responding to conversational greetings, explaining a concept, or asking for clarification. It should call a tool the moment a deterministic calculation, factual lookup, or file generation (like a plot) is required to accurately fulfill the prompt.