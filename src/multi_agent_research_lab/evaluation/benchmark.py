"""Benchmark suite for single-agent vs multi-agent research systems."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def compute_citation_coverage(state: ResearchState) -> float:
    """Calculate the ratio of retrieved sources referenced in the final answer."""
    if not state.sources or not state.final_answer:
        return 0.0

    cited_count = 0
    for i, source in enumerate(state.sources):
        citation_tag = f"[{i+1}]"
        if citation_tag in state.final_answer or (
            source.title
            and len(source.title) > 10
            and source.title.lower() in state.final_answer.lower()
        ):
            cited_count += 1

    return min(1.0, cited_count / len(state.sources))


def compute_quality_score(state: ResearchState) -> float:
    """Heuristic quality scoring based on structure, depth, citations, and analytical rigor."""
    if not state.final_answer:
        return 0.0

    score = 5.0
    ans = state.final_answer

    word_count = len(ans.split())
    if word_count >= 250:
        score += 1.5
    elif word_count >= 100:
        score += 0.8

    if "###" in ans or "####" in ans or "**" in ans:
        score += 1.5

    if re.search(r"\[\d+\]", ans) or "References" in ans or "Sources:" in ans:
        score += 1.5

    if state.analysis_notes:
        score += 0.5

    return min(10.0, round(score, 1))


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Execute a runner, measure metrics, and return results."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    cost_usd = sum(
        float(res.metadata.get("cost_usd", 0.0) or 0.0) for res in state.agent_results
    )

    citation_cov = compute_citation_coverage(state)
    quality = compute_quality_score(state)
    failure_rate = 0.0 if (state.final_answer and len(state.final_answer) > 20) else 1.0

    notes = f"Iterations: {state.iteration}, Sources: {len(state.sources)}"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=round(latency, 2),
        estimated_cost_usd=round(cost_usd, 6),
        quality_score=quality,
        citation_coverage=round(citation_cov, 2),
        failure_rate=failure_rate,
        notes=notes,
    )
    return state, metrics
