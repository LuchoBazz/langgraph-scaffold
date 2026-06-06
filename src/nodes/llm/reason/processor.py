"""
Reason LLM node
"""

import asyncio
from typing import Any, Dict
from src.base import BaseLLMNode, NodeExecutionError
from .prompts import get_prompts

class ReasonLLMNode(BaseLLMNode):
    """
    Reason LLM node implementation
    
    This node processes input using LLM capabilities for the reason functionality.
    Customize the run() method to implement your specific LLM logic and AI system calls.
    """
    
    def __init__(self, config):
        super().__init__(config, "reason")
        # Load node-specific prompts
        self.node_prompts = get_prompts()
    
    async def run(self, input_data: Any) -> Any:
        """
        Execute the reason LLM logic with comprehensive error recovery.
        
        Args:
            input_data: Input data to process with LLM
            
        Returns:
            LLM-processed result
            
        Raises:
            NodeExecutionError: If all recovery attempts fail
        """
        max_retries = 3
        retry_delay = 2.0  # Longer delay for LLM calls
        
        for attempt in range(max_retries):
            try:
                # Validate input
                if not self.validate_input(input_data):
                    raise ValueError(f"Invalid input data for {self.node_name}")
                
                # Execute with timeout (longer for LLM calls)
                result = await self._execute_reason_llm_logic(input_data)
                
                # Validate output
                if not self.validate_output(result):
                    raise ValueError(f"Invalid output from {self.node_name}")
                
                return result
                
            except (ValueError, TypeError) as e:
                # Validation errors - don't retry
                print(f"❌ Validation error in {self.node_name}: {e}")
                raise NodeExecutionError(f"Validation failed in {self.node_name}: {e}")
                
            except Exception as e:
                print(f"⚠️ LLM error in {self.node_name} (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    error_msg = f"Failed to execute {self.node_name} after {max_retries} attempts: {e}"
                    print(f"❌ {error_msg}")
                    raise NodeExecutionError(error_msg)
                
                # Exponential backoff with longer delays for LLM
                await asyncio.sleep(retry_delay * (2 ** attempt))
        
        raise NodeExecutionError(f"Unexpected error in {self.node_name} execution")
    
    async def _execute_reason_llm_logic(self, data: Any) -> Any:
        """
        Execute the specific reason LLM logic
        
        This method should call your AI system with the appropriate prompts.
        Customize this method to implement your specific LLM integration:
        
        - OpenAI API calls
        - Ollama local model calls  
        - Anthropic Claude API calls
        - Custom model endpoints
        - Prompt engineering and response processing
        
        Available prompts: {list(self.prompts.keys())}
        Model configuration: {self.model_config}
        """        
        # Get the appropriate prompt for this node
        system_prompt = self.prompts.get("system", "You are a helpful AI assistant.")
        user_prompt = self.prompts.get("user_template", "Process the following input: {input}")
        
        # LLM integration based on configured provider
        model_name = self.model_config.get("name", "gpt-4")
        
        # Fallback for unknown providers or mock mode
        formatted_prompt = user_prompt.format(input=str(data))
        return {
            "node": self.node_name,
            "llm_response": f"Mock LLM response for {self.node_name}: processed '{data}'",
            "model_used": f"mock/mock-llm",
            "prompt_used": system_prompt[:50] + "...",
            "input_processed": data
        }
