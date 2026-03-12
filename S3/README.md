## Week 3: Function Calling, Tools, and LLMs That Can Act

# Part 2: Guided Demo — The Three Little Pigs

1. Three Little Pigs demo test
9
• Explain how you configured the demo with the API details from
week-03/code/apikey.md
• Show evidence that you ran both scenarios
• Explain what changed when tools were enabled
2. Function calling explanation
• In your own words, explain how function calling works
• Explain the difference between a normal assistant answer and a tool
call
• Explain why the host program remains in control
3. Math solver design
• Describe your chosen tools
• Explain why you limited the tool set
• Show key code fragments and explain them
4. Testing evidence
• Include several math problems you tried
• Show at least one successful plot saved as .png
• Show at least one failure case and how your program handled it
5. Reflection
• What did the model do well?
• Where did it choose tools badly or fail?
• What did you learn about using LLMs as orchestrators rather than
calculators?
Required Questions to Answer in the Report
Answer these explicitly:
1. Why is function calling more reliable than asking the model to “just do
the math” in plain text?
2. Why should the available tool set be small and well-defined?
3. What is the role of sympy in your solution?
4. What is the role of matplotlib in your solution?
5. What happens in your program from the moment the user types a problem
to the final answer?
6. What kinds of errors can still happen even when function calling is used?
7. When should the model answer directly, and when should it call a tool?