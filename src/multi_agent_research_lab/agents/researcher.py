"""Researcher agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        search_client: SearchClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        sources = self.search_client.search(
            query=state.request.query,
            max_results=state.request.max_sources,
        )
        state.sources = sources

        sources_text = "\n\n".join(
            f"Source [{i + 1}] {doc.title} ({doc.url or 'N/A'}):\n{doc.snippet}"
            for i, doc in enumerate(sources)
        )

        system_prompt = (
            "You are a Senior Researcher Agent. Your responsibility is to analyze retrieved "
            "sources and create concise, structured, factual research notes relevant to the query."
        )
        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Retrieved Sources:\n{sources_text}\n\n"
            "Please provide comprehensive research notes covering core concepts and findings."
        )

        response = self.llm_client.complete(system_prompt, user_prompt)
        state.research_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "source_count": len(sources),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event(
            "researcher_finished",
            {"source_count": len(sources), "cost_usd": response.cost_usd},
        )

        return state
