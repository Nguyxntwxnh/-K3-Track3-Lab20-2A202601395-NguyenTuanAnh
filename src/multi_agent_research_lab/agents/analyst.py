"""Analyst agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        if not state.research_notes:
            state.analysis_notes = "No research notes provided for analysis."
            return state

        system_prompt = (
            "You are an Expert Systems Analyst Agent. Your task is to critically evaluate "
            "the provided research notes, compare technical trade-offs, and synthesize insights."
        )
        user_prompt = (
            f"Original Query: {state.request.query}\n"
            f"Target Audience: {state.request.audience}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            "Please deliver a structured critical analysis covering key architectural trade-offs."
        )

        response = self.llm_client.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event(
            "analyst_finished",
            {"cost_usd": response.cost_usd},
        )

        return state
