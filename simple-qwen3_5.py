from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "Qwen/Qwen3.5-14B" 
DEVICE = "cuda"
DTYPE = torch.bfloat16  # A100 supports BF16 very well

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=DTYPE,
    device_map="cuda",
    low_cpu_mem_usage=True,
)

model.eval()
print(f"Qwen CLI on {DEVICE} ({DTYPE}) (Ctrl+C to quit)")

while True:
    try:
        user = input("\n> ").strip()
        if not user:
            continue

        messages = [{"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )

        print("\n" + tokenizer.decode(output[0], skip_special_tokens=True))

    except KeyboardInterrupt:
        print("\nBye.")
        break