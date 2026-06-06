"""
Prompt definitions for the act LLM node
"""

from typing import Dict, Any

def get_prompts() -> Dict[str, Any]:
    """
    Define prompts for the act LLM node.
    
    Customize these prompts for your specific use case.
    
    Returns:
        Dictionary containing prompt templates
    """
    return {
        "system": """You are a helpful AI assistant specialized in act tasks.""",

        "user_template": """Process the following input for the act LLM stage:

Input: {input}

Context: {context}

Please provide a structured response that can be used by the next stage in the pipeline."""
    }
