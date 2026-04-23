"""LangGraph ReAct agent graph. Builds a START → call_model ↔ tools loop."""
from __future__ import annotations

from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.tool_loader import as_langchain_tools
from app.core.config import settings


def build_graph():
    """Build and compile the LangGraph ReAct graph. Call once at startup."""
    lc_tools = as_langchain_tools()

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0,
    ).bind_tools(lc_tools)

    tool_node = ToolNode(lc_tools)

    async def call_model(state: AgentState) -> dict:
        response: BaseMessage = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("call_model", call_model)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "call_model")
    graph.add_conditional_edges(
        "call_model",
        should_continue,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "call_model")

    return graph.compile()


# Module-level singleton: stateless, safe for concurrent async requests.
_graph = build_graph()


def get_graph():
    return _graph
