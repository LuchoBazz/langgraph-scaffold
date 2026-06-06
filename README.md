# Lang Graph Scaffold

An AI agent built with langgraph and python.

## Project Structure

```
src/
├── nodes/           # Agent execution nodes
│   ├── act/reason/retrieve/
│   │   ├── logic.py    # Node execution logic
│   │   └── prompts.py   # Prompt definitions
├── main.py             # Main application entry
└── config.py          # Configuration
```

## Features

- **Runtime**: fastapi
- **Framework**: langgraph
- **Orchestration**: state-graph
- **Tools**: http_fetch, calculator
- **Model**: mock/mock-llm
- **Storage**: faiss-local/in-memory/sqlite

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the agent:
   ```bash
   python main.py
   ```

## Customization

Each node in `src/nodes/` contains:
- `logic.*`: The execution logic for the node
- `prompts.*`: Prompt definitions and templates

Edit these files to customize your agent's behavior.
