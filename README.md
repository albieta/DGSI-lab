Install Script 

```
# Install all packages first
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv \
git curl wget sqlite3 vim nano htop tree jq build-essential python3-dev

# Python tools
pip3 install llm anthropic openai transformers pydantic requests
pip3 install  torch --index-url https://download.pytorch.org/whl/cpu

# Pre-cache GPT-2 model (~500MB)
python3 -c "from transformers import pipeline, AutoTokenizer;
pipeline('text-generation', model='gpt2');
print('GPT-2 cached successfully')"

pip3 install chromadb

sudo apt install -y nodejs npm
pip3 install mcp

sudo snap install astral-uv --classic
```

Create Project

```
uv init .
uv add transformers torch accelerate

# create gpt2_cli.py file with code
uv run python gpt2_cli.py
```