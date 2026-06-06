"""
Graph orchestration for Lang Graph Scaffold LangGraph
This file handles how nodes interact with each other and wraps node classes as LangGraph functions.
"""

from typing import Dict, Any, Callable
from langchain_core.messages import AIMessage
import asyncio

from ...config import Config
from ...state import AgentState, set_stage_result, add_message, set_error, clear_error

# Import node classes from /src/nodes/
from ...nodes.llm.act.processor import ActLLMNode
from ...nodes.llm.reason.processor import ReasonLLMNode
from ...nodes.llm.retrieve.processor import RetrieveLLMNode


# Global node instances (initialized once)
_node_instances = {}

def _get_node_instance(node_name: str, node_type: str = "llm"):
    """
    Get or create a node instance (singleton pattern).
    
    Args:
        node_name: Name of the node
        node_type: Type of node ('llm' or 'tool')
        
    Returns:
        Node instance
    """
    global _node_instances
    key = f"{node_name}_{node_type}"
    
    if key not in _node_instances:
        config = Config()
        if node_type == "llm":
            # Dynamic import for LLM nodes
            class_name = f"{''.join(word.capitalize() for word in node_name.replace('-', '_').split('_'))}LLMNode"
            module_path = f"src.nodes.llm.{node_name.replace('-', '_')}.processor"
            module = __import__(module_path, fromlist=[class_name])
            node_class = getattr(module, class_name)
            _node_instances[key] = node_class(config)
        else:
            # Dynamic import for Tool nodes
            class_name = f"{''.join(word.capitalize() for word in node_name.replace('-', '_').split('_'))}ToolNode"
            module_path = f"src.nodes.tools.{node_name.replace('-', '_')}.processor"
            module = __import__(module_path, fromlist=[class_name])
            node_class = getattr(module, class_name)
            _node_instances[key] = node_class(config)
    
    return _node_instances[key]

# LangGraph node functions that wrap node classes

async def act_node(state: AgentState) -> AgentState:
    """
    LangGraph wrapper for Act LLM node.
    This function handles graph orchestration and calls the actual node class.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with act results
    """
    try:
        # Get node instance (singleton)
        node_instance = _get_node_instance("act", "llm")
        
        # Get input data for processing
        input_data = state.get("input", "")
        
        # Get previous stage results if available
        previous_results = ""
        if state.get("results"):
            stages = ["act","reason","retrieve"]
            current_index = stages.index("act") if "act" in stages else -1
            if current_index > 0:
                prev_stage = stages[current_index - 1]
                previous_results = state["results"].get(prev_stage, "")
        
        # Prepare input for the node class
        processing_input = previous_results if previous_results else str(input_data)
        
        # Call the actual node class
        result = await node_instance.run(processing_input)
        
        # Update state with results
        state = set_stage_result(state, "act", result)
        
        # Add AI message
        message = AIMessage(content=f"Act: {result}")
        state = add_message(state, message)
        
        return state
        
    except Exception as e:
        error_msg = f"Act node error: {str(e)}"
        print(f"❌ {error_msg}")
        return set_error(state, error_msg)

async def reason_node(state: AgentState) -> AgentState:
    """
    LangGraph wrapper for Reason LLM node.
    This function handles graph orchestration and calls the actual node class.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with reason results
    """
    try:
        # Get node instance (singleton)
        node_instance = _get_node_instance("reason", "llm")
        
        # Get input data for processing
        input_data = state.get("input", "")
        
        # Get previous stage results if available
        previous_results = ""
        if state.get("results"):
            stages = ["act","reason","retrieve"]
            current_index = stages.index("reason") if "reason" in stages else -1
            if current_index > 0:
                prev_stage = stages[current_index - 1]
                previous_results = state["results"].get(prev_stage, "")
        
        # Prepare input for the node class
        processing_input = previous_results if previous_results else str(input_data)
        
        # Call the actual node class
        result = await node_instance.run(processing_input)
        
        # Update state with results
        state = set_stage_result(state, "reason", result)
        
        # Add AI message
        message = AIMessage(content=f"Reason: {result}")
        state = add_message(state, message)
        
        return state
        
    except Exception as e:
        error_msg = f"Reason node error: {str(e)}"
        print(f"❌ {error_msg}")
        return set_error(state, error_msg)

async def retrieve_node(state: AgentState) -> AgentState:
    """
    LangGraph wrapper for Retrieve LLM node.
    This function handles graph orchestration and calls the actual node class.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with retrieve results
    """
    try:
        # Get node instance (singleton)
        node_instance = _get_node_instance("retrieve", "llm")
        
        # Get input data for processing
        input_data = state.get("input", "")
        
        # Get previous stage results if available
        previous_results = ""
        if state.get("results"):
            stages = ["act","reason","retrieve"]
            current_index = stages.index("retrieve") if "retrieve" in stages else -1
            if current_index > 0:
                prev_stage = stages[current_index - 1]
                previous_results = state["results"].get(prev_stage, "")
        
        # Prepare input for the node class
        processing_input = previous_results if previous_results else str(input_data)
        
        # Call the actual node class
        result = await node_instance.run(processing_input)
        
        # Update state with results
        state = set_stage_result(state, "retrieve", result)
        
        # Add AI message
        message = AIMessage(content=f"Retrieve: {result}")
        state = add_message(state, message)
        
        return state
        
    except Exception as e:
        error_msg = f"Retrieve node error: {str(e)}"
        print(f"❌ {error_msg}")
        return set_error(state, error_msg)


async def finalizer_node(state: AgentState) -> AgentState:
    """
    Finalizer node that merges results from parallel execution.
    
    This node consolidates all results from parallel branches and prepares
    the final output for the agent. It's automatically included in all agents
    to enable parallelization and data merging.
    
    Args:
        state: Current agent state with results from all parallel nodes
        
    Returns:
        Updated state with merged final results
    """
    try:
        from datetime import datetime
        from langchain_core.messages import AIMessage
        
        # Get all results from parallel execution
        all_results = state.get("results", {})
        
        # Merge all results into a final output
        final_output = {
            "merged_results": all_results,
            "execution_summary": {
                "total_stages": len(all_results),
                "completed_stages": list(all_results.keys()),
                "finalization_timestamp": datetime.now().isoformat()
            }
        }
        
        # Create new state without circular references
        updated_results = dict(state.get("results", {}))
        updated_results["finalizer"] = final_output
        
        updated_messages = list(state.get("messages", []))
        final_message = AIMessage(content=f"Finalizer: Merged results from {len(all_results)} parallel stages")
        updated_messages.append(final_message)
        
        # Return new state with proper structure
        return {
            "input": state.get("input"),
            "messages": updated_messages,
            "context": state.get("context", {}),
            "results": updated_results,
            "current_stage": "finalizer",
            "error": state.get("error"),
            "metadata": state.get("metadata", {})
        }
        
    except Exception as e:
        # Handle finalizer errors gracefully
        return {
            "input": state.get("input"),
            "messages": state.get("messages", []),
            "context": state.get("context", {}),
            "results": state.get("results", {}),
            "current_stage": "finalizer",
            "error": f"Finalizer error: {str(e)}",
            "metadata": state.get("metadata", {})
        }

def get_graph_nodes(config: Config) -> Dict[str, Callable]:
    """
    Get graph nodes based on configuration.
    Dynamically returns nodes based on user's LLM and tool node configuration.
    Always includes a finalizer node for parallel execution and data merging.
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary of node functions including finalizer
    """
    node_functions = {}
    
    # Add LLM nodes
    node_functions["act"] = act_node
    node_functions["reason"] = reason_node
    node_functions["retrieve"] = retrieve_node

    
    # Add Tool nodes  

    
    # Always add finalizer node for parallel execution and data merging
    node_functions["finalizer"] = finalizer_node
    
    # Return all nodes including finalizer
    return node_functions

def create_custom_node(stage_name: str, logic_func: Callable) -> Callable:
    """
    Create a custom node function.
    
    Args:
        stage_name: Name of the stage
        logic_func: Logic function for the node
        
    Returns:
        Node function
    """
    async def custom_node(state: AgentState) -> AgentState:
        try:
            clear_error(state)
            result = await logic_func(state)
            state = set_stage_result(state, stage_name, result)
            return state
        except Exception as e:
            return set_error(state, f"{stage_name} error: {str(e)}")
    
    return custom_node
