# Retrieve LLM Node

This folder contains the implementation for the **retrieve** LLM node of the Lang Graph Scaffold agent.

## Files

- **`processor.py`** - Contains the main processing logic for this LLM node
- **`prompts.py`** - Contains prompt definitions and templates
- **`__init__.py`** - Makes this directory a Python package

## Purpose

The retrieve LLM node is responsible for:
- Processing data using Large Language Model capabilities
- Applying prompts and generating intelligent responses
- Providing AI-powered reasoning and analysis

## Model Configuration

This LLM node uses:
- **Provider**: mock
- **Model**: Default model

## Usage

```python
from src.nodes.llm.retrieve.processor import RetrieveLLMNode

# Initialize the LLM node
node = RetrieveLLMNode(config)

# Run the LLM node
result = await node.run(input_data)

# Get model information
model_info = node.get_model_info()
```

## Configuration

This LLM node uses the following configuration:
- **Type**: LLM Node
- **Model**: Node-specific model configuration
- **Prompts**: Custom prompt templates
- **Storage**: faiss-local/in-memory/sqlite

## Customization

To customize this LLM node:

1. **Modify Processor**: Edit `processor.py` to change the LLM processing behavior
2. **Update Prompts**: Edit `prompts.py` to modify prompt templates
3. **Change Model**: Update the model configuration for this specific node
4. **Add Context**: Enhance prompts with additional context


