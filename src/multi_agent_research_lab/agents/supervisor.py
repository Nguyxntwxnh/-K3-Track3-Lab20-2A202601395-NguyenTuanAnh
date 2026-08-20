"""Supervisor / router implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, max_iterations: int | None = None) -> None:
        settings = get_settings()
        self.max_iterations = max_iterations or settings.max_iterations

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        # 1. Guardrail: Max iterations check
        if state.iteration >= self.max_iterations:
            next_route = "done"
            state.record_route(next_route)
            state.add_trace_event(
                "supervisor_max_iterations_reached", {"iteration": state.iteration}
            )
            return state

        # 2. Decision Logic based on state completeness
        if not state.sources or not state.research_notes:
            next_route = "researcher"
        elif not state.analysis_notes:
            next_route = "analyst"
        elif not state.final_answer:
            next_route = "writer"
        else:
            next_route = "done"

        # 3. Record decision
        state.record_route(next_route)
        state.add_trace_event(
            "supervisor_routed",
            {"next_route": next_route, "iteration": state.iteration},
        )
        return state
