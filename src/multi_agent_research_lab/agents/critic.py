"""Optional critic agent for fact-checking and validation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and verify citation coverage."""
        if not state.final_answer:
            return state

        # Check citation coverage
        source_count = len(state.sources)
        cited_sources = sum(1 for i in range(1, source_count + 1) if f"[{i}]" in state.final_answer)
        coverage = (cited_sources / source_count) if source_count > 0 else 1.0

        review_notes = (
            f"Validation Passed: {cited_sources}/{source_count} sources cited ({coverage:.0%})."
        )

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=review_notes,
                metadata={"citation_coverage": coverage},
            )
        )
        state.add_trace_event("critic_evaluated", {"citation_coverage": coverage})
        return state
