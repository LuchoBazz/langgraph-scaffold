"""
Main LangGraph for Lang Graph Scaffold
"""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import asyncio

class GraphExecutionError(Exception):
    """Custom exception for graph execution errors"""
    pass

from ..config import Config
from ..state import AgentState
from .nodes import get_graph_nodes

class LangGraphScaffoldGraph:
    def __init__(self, config: Config):
        self.config = config
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph from configuration.
        
        Returns:
            Configured StateGraph instance
        """
        # Create the graph
        graph = StateGraph(AgentState)
        
        # Add nodes from graph configuration
        nodes = get_graph_nodes(self.config)
        
        for node_id, node_config in self.config.graph_config.get("nodes", {}).items():
            if node_id in nodes:
                graph.add_node(node_id, nodes[node_id])
        
        # Always ensure finalizer node is available for parallel execution
        # This is required for all agents to enable parallelization and data merging
        if "finalizer" not in self.config.graph_config.get("nodes", {}):
            if "finalizer" in nodes:
                graph.add_node("finalizer", nodes["finalizer"])
            else:
                # Create a default finalizer node if none exists
                graph.add_node("finalizer", self._create_default_finalizer_node())
        
        # Add edges from graph configuration
        self._add_configured_edges(graph)
        
        # Compile the graph
        return graph.compile()
    
    def _add_configured_edges(self, graph: StateGraph):
        """
        Add edges from graph configuration.
        
        Args:
            graph: StateGraph instance
        """
        graph_config = self.config.graph_config
        
        # Add regular edges
        for edge in graph_config.get("edges", []):
            from_node = edge["from"]
            to_node = edge["to"]
            
            if from_node == "START":
                graph.add_edge(START, to_node)
            elif to_node == "END":
                graph.add_edge(from_node, END)
            else:
                graph.add_edge(from_node, to_node)
        
        # Add conditional edges
        for conditional_edge in graph_config.get("conditional_edges", []):
            from_node = conditional_edge["from"]
            condition_func = conditional_edge.get("condition", "default_condition")
            routes = conditional_edge.get("routes", [])
            
            # Create route mapping
            route_map = {}
            for route in routes:
                condition = route["condition"]
                to_node = route["to"]
                if to_node == "END":
                    route_map[condition] = END
                else:
                    route_map[condition] = to_node
            
            # Add conditional edge
            graph.add_conditional_edges(
                from_node,
                getattr(self, f"_{condition_func}", self._default_condition),
                route_map
            )
    
    def _default_condition(self, state: AgentState) -> str:
        """
        Default condition function for conditional edges.
        
        Args:
            state: Current agent state
            
        Returns:
            Condition string
        """
        return "continue"
    
    def _add_pipeline_edges(self, graph: StateGraph):
        """
        Add edges for pipeline-style orchestration (sequential).
        
        Args:
            graph: StateGraph instance
        """
        stages = self.config.agent_stages
        
        # Add edges in sequence
        for i in range(len(stages) - 1):
            graph.add_edge(stages[i], stages[i + 1])
        
        # Add edge from last stage to END
        if stages:
            graph.add_edge(stages[-1], END)
    
    def _add_router_edges(self, graph: StateGraph):
        """
        Add edges for router-style orchestration (branching).
        
        Args:
            graph: StateGraph instance
        """
        stages = self.config.agent_stages
        
        if len(stages) >= 2:
            # First stage routes to others
            graph.add_edge(stages[0], stages[1])
            
            # Add conditional routing logic
            # TODO: Implement conditional routing based on state
            for i in range(1, len(stages)):
                graph.add_edge(stages[i], END)
    
    def _add_state_graph_edges(self, graph: StateGraph):
        """
        Add edges for state-graph orchestration (complex state management).
        
        Args:
            graph: StateGraph instance
        """
        stages = self.config.agent_stages
        
        if not stages:
            return
            
        # Add entrypoint from START to first stage
        graph.add_edge(START, stages[0])
        
        # Add edges with conditional logic
        for i, stage in enumerate(stages):
            if i < len(stages) - 1:
                # Add conditional edge to next stage or END
                graph.add_conditional_edges(
                    stage,
                    self._get_next_stage,
                    {
                        "continue": stages[i + 1] if i + 1 < len(stages) else END,
                        "end": END
                    }
                )
            else:
                graph.add_edge(stage, END)
    
    def _get_next_stage(self, state: AgentState) -> str:
        """
        Determine the next stage based on current state.
        
        Args:
            state: Current agent state
            
        Returns:
            Next stage name or "end"
        """
        # TODO: Implement conditional logic based on state
        # For now, always continue to next stage
        return "continue"
    
    def _create_default_finalizer_node(self):
        """
        Create a default finalizer node for merging parallel execution results.
        
        Returns:
            Finalizer node function
        """
        async def finalizer_node(state: AgentState) -> AgentState:
            """
            Default finalizer node that merges results from parallel execution.
            
            This node consolidates all results from parallel branches and prepares
            the final output for the agent.
            
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
        
        return finalizer_node
    
    
    async def execute(self, input_data: Any) -> Any:
        """
        Execute the graph with input data and comprehensive error recovery.
        
        Args:
            input_data: Input data for the graph
            
        Returns:
            Graph execution result
            
        Raises:
            GraphExecutionError: If all recovery attempts fail
        """
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                # Validate input
                if not self._validate_graph_input(input_data):
                    raise ValueError("Invalid input data for graph execution")
                
                # Prepare initial state
                initial_state = {
                    "input": input_data,
                    "messages": [HumanMessage(content=str(input_data))],
                    "context": {},
                    "results": {},
                    "current_stage": self.config.agent_stages[0] if self.config.agent_stages else None,
                    "error": None,
                    "metadata": {"attempt": attempt + 1, "max_retries": max_retries}
                }
                
                # Execute the graph with timeout
                result = await asyncio.wait_for(
                    self.graph.ainvoke(initial_state),
                    timeout=120.0  # 2 minutes for full graph execution
                )
                
                # Validate result
                if not self._validate_graph_output(result):
                    raise ValueError("Invalid output from graph execution")
                
                return result
                
            except (ValueError, TypeError) as e:
                # Validation errors - don't retry
                print(f"❌ Graph validation error (attempt {attempt + 1}): {e}")
                raise GraphExecutionError(f"Graph validation failed: {e}")
                
            except asyncio.TimeoutError:
                print(f"⏰ Graph execution timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise GraphExecutionError(f"Graph execution timeout after {max_retries} attempts")
                await asyncio.sleep(retry_delay * (attempt + 1))
                
            except Exception as e:
                print(f"⚠️ Graph execution error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    error_msg = f"Graph execution failed after {max_retries} attempts: {e}"
                    print(f"❌ {error_msg}")
                    raise GraphExecutionError(error_msg)
                
                # Exponential backoff
                await asyncio.sleep(retry_delay * (2 ** attempt))
        
        raise GraphExecutionError("Unexpected error in graph execution")
    
    def _validate_graph_input(self, input_data: Any) -> bool:
        """Validate input data for graph execution"""
        if input_data is None:
            return False
        
        if isinstance(input_data, str):
            return len(input_data.strip()) > 0 and len(input_data) <= 50000
        elif isinstance(input_data, dict):
            return bool(input_data)
        elif isinstance(input_data, list):
            return len(input_data) > 0 and len(input_data) <= 1000
        
        return True
    
    def _validate_graph_output(self, result: Any) -> bool:
        """Validate output from graph execution"""
        if result is None:
            return False
        
        # Check if result has expected structure
        if isinstance(result, dict):
            # Should have at least some results
            return "results" in result or "messages" in result
        
        return True
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        Get information about the graph structure.
        
        Returns:
            Graph information dictionary
        """
        return {
            "nodes": list(self.graph.nodes.keys()) if hasattr(self.graph, 'nodes') else [],
            "edges": [],  # CompiledStateGraph doesn't expose edges directly
            "orchestration_style": "state-graph",
            "stages": self.config.agent_stages
        }

def create_graph(config: Config) -> LangGraphScaffoldGraph:
    """
    Create and return a configured graph instance.
    
    Args:
        config: Configuration object
        
    Returns:
        Configured graph instance
    """
    return LangGraphScaffoldGraph(config)
