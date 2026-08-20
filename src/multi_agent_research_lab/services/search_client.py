"""Search client abstraction for ResearcherAgent."""

import json
import os
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client supporting Tavily and Mock search fallback."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.tavily_api_key or os.getenv("TAVILY_API_KEY")

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if self.api_key:
            try:
                return self._search_tavily(query, max_results)
            except Exception:
                return self._search_mock(query, max_results)
        return self._search_mock(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Search using Tavily API."""
        url = "https://api.tavily.com/search"
        payload = json.dumps({
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_raw_content": False,
        }).encode("utf-8")

        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        results: list[SourceDocument] = []
        for item in data.get("results", []):
            results.append(
                SourceDocument(
                    title=item.get("title", "Untitled Source"),
                    url=item.get("url"),
                    snippet=item.get("content", ""),
                    metadata={"score": item.get("score", 1.0), "source": "tavily"},
                )
            )
        return results

    def _search_mock(self, query: str, max_results: int) -> list[SourceDocument]:
        """Mock search returning relevant synthetic sources for development and testing."""
        query_lower = query.lower()

        if "graphrag" in query_lower:
            mock_data = [
                {
                    "title": "From Local to Global: A Graph RAG Approach to Summarization",
                    "url": "https://arxiv.org/abs/2404.16130",
                    "snippet": (
                        "Microsoft Research introduces GraphRAG, combining knowledge graphs with "
                        "LLMs for hierarchical community detection and summarization."
                    ),
                },
                {
                    "title": "Graph Retrieval-Augmented Generation: A Survey",
                    "url": "https://arxiv.org/abs/2408.08921",
                    "snippet": (
                        "Surveys graph-enhanced retrieval paradigms. Compares standard vector "
                        "retrieval with graph-based indexing and relation mapping."
                    ),
                },
                {
                    "title": "Evaluating GraphRAG Systems in Production",
                    "url": "https://techcommunity.microsoft.com/graphrag-evaluation",
                    "snippet": (
                        "Key metrics for GraphRAG include global sensemaking comprehensiveness, "
                        "hallucination reduction, and token cost trade-offs."
                    ),
                },
            ]
        elif "guardrail" in query_lower:
            mock_data = [
                {
                    "title": "Building Effective and Safe LLM Agents",
                    "url": "https://www.anthropic.com/research/building-effective-agents",
                    "snippet": (
                        "Defines core agent architectures and emphasizes minimal sufficient "
                        "guardrails: loop limits, execution timeouts, and validators."
                    ),
                },
                {
                    "title": "Reliability Engineering for Multi-Agent Systems",
                    "url": "https://arxiv.org/abs/2402.12345",
                    "snippet": (
                        "Production multi-agent deployments suffer from infinite looping. "
                        "Implementing hard iteration bounds reduces failure rates."
                    ),
                },
            ]
        else:
            mock_data = [
                {
                    "title": f"Technical Overview: {query}",
                    "url": "https://docs.research-lab.ai/topic-overview",
                    "snippet": f"Foundational concepts and industry adoption for {query}.",
                },
                {
                    "title": f"Architectural Patterns for {query}",
                    "url": "https://engineering.research-lab.ai/architectures",
                    "snippet": f"Comparative trade-off analysis and cost for {query}.",
                },
            ]

        results: list[SourceDocument] = []
        for item in mock_data[:max_results]:
            results.append(
                SourceDocument(
                    title=item["title"],
                    url=item["url"],
                    snippet=item["snippet"],
                    metadata={"source": "mock_search"},
                )
            )
        return results
