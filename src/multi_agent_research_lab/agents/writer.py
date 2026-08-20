"""Writer agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        sources_summary = "\n".join(
            f"[{i+1}] {doc.title} ({doc.url or 'N/A'})"
            for i, doc in enumerate(state.sources)
        )

        system_prompt = (
            "You are a Lead Technical Writer Agent. Your task is to craft a comprehensive, "
            "polished and authoritative final answer addressing the user query. Incorporate "
            "facts from research notes and analytical evaluations. Ensure inline citations [1]."
        )
        user_prompt = (
            f"User Query: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Available Sources:\n{sources_summary}\n\n"
            f"Research Notes:\n{state.research_notes or 'N/A'}\n\n"
            f"Analysis Notes:\n{state.analysis_notes or 'N/A'}\n\n"
            "Please compose the final structured summary complete with citations."
        )

        response = self.llm_client.complete(system_prompt, user_prompt, temperature=0.3)
        state.final_answer = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event(
            "writer_finished",
            {"cost_usd": response.cost_usd},
        )

        return state
