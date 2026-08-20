"""LangGraph workflow implementation."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph with LangGraph."""

    def __init__(self) -> None:
        settings = get_settings()
        self.supervisor = SupervisorAgent(max_iterations=settings.max_iterations)
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.graph = self.build()

    def build(self) -> Any:
        """Create and compile the LangGraph workflow."""
        builder = StateGraph(ResearchState)

        # 1. Add agent nodes
        builder.add_node("supervisor", lambda state: self.supervisor.run(state))
        builder.add_node("researcher", lambda state: self.researcher.run(state))
        builder.add_node("analyst", lambda state: self.analyst.run(state))
        builder.add_node("writer", lambda state: self.writer.run(state))

        # 2. Entry point
        builder.add_edge(START, "supervisor")

        # 3. Conditional routing from supervisor
        def route_decision(state: ResearchState) -> str:
            if not state.route_history:
                return END
            last_route = state.route_history[-1]
            if last_route in ("researcher", "analyst", "writer"):
                return last_route
            return END

        builder.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                END: END,
            },
        )

        # 4. Handoff back to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return the updated state."""
        result = self.graph.invoke(state)
        if isinstance(result, ResearchState):
            return result
        if isinstance(result, dict):
            return ResearchState.model_validate(result)
        return state
