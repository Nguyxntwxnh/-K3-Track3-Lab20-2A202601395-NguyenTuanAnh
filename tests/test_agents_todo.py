"""Unit tests for agents and supervisor routing policy."""

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain GraphRAG state of the art"))
    supervisor = SupervisorAgent()
    state = supervisor.run(state)
    assert state.route_history[-1] == "researcher"


def test_supervisor_routes_to_analyst_when_sources_present() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain GraphRAG state of the art"),
        sources=[SourceDocument(title="Test Doc", snippet="Test snippet")],
        research_notes="Found relevant notes.",
    )
    supervisor = SupervisorAgent()
    state = supervisor.run(state)
    assert state.route_history[-1] == "analyst"


def test_supervisor_routes_to_writer_when_analysis_present() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain GraphRAG state of the art"),
        sources=[SourceDocument(title="Test Doc", snippet="Test snippet")],
        research_notes="Found relevant notes.",
        analysis_notes="Analyzed insights.",
    )
    supervisor = SupervisorAgent()
    state = supervisor.run(state)
    assert state.route_history[-1] == "writer"


def test_supervisor_stops_at_max_iterations() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain GraphRAG state of the art"),
        iteration=6,
    )
    supervisor = SupervisorAgent(max_iterations=6)
    state = supervisor.run(state)
    assert state.route_history[-1] == "done"


def test_researcher_populates_sources_and_notes() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain GraphRAG state of the art"))
    researcher = ResearcherAgent()
    state = researcher.run(state)
    assert len(state.sources) > 0
    assert state.research_notes is not None


def test_analyst_and_writer_complete() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain GraphRAG state of the art"),
        sources=[SourceDocument(title="Test Doc", snippet="Test snippet")],
        research_notes="Found relevant notes.",
    )
    analyst = AnalystAgent()
    state = analyst.run(state)
    assert state.analysis_notes is not None

    writer = WriterAgent()
    state = writer.run(state)
    assert state.final_answer is not None
