"""Command-line entrypoint for the lab starter."""

import sys
from time import perf_counter
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import init_tracing
from multi_agent_research_lab.services.llm_client import LLMClient

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console(force_terminal=True, legacy_windows=False)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_tracing()


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a real single-agent baseline end-to-end and report metrics."""
    _init()
    request = _parse_query(query)
    state = ResearchState(request=request)
    llm_client = LLMClient()

    console.print(f"[bold cyan]Running Single-Agent Baseline for query:[/bold cyan] {query}")

    system_prompt = (
        "You are an all-in-one AI research assistant. Directly answer the user query in a "
        "structured, comprehensive, and authoritative manner. Provide key concepts, architectural "
        "mechanisms, trade-offs, and practical conclusions."
    )
    user_prompt = f"Please research and synthesize an answer for: {request.query}"

    started = perf_counter()
    response = llm_client.complete(system_prompt, user_prompt)
    latency = perf_counter() - started

    state.final_answer = response.content
    state.agent_results.append(
        AgentResult(
            agent=AgentName.SUPERVISOR,
            content=response.content,
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "latency_seconds": latency,
            },
        )
    )

    console.print(
        Panel(
            state.final_answer or "No answer",
            title="Single-Agent Baseline Response",
            border_style="green",
        )
    )
    console.print(
        f"[dim]Latency: [bold]{latency:.2f}s[/bold] | "
        f"Tokens: {response.input_tokens or 0} in / {response.output_tokens or 0} out | "
        f"Estimated Cost: ${response.cost_usd or 0:.6f}[/dim]"
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent LangGraph workflow."""
    _init()
    request = _parse_query(query)
    state = ResearchState(request=request)
    workflow = MultiAgentWorkflow()

    console.print(f"[bold green]Starting Multi-Agent Workflow for query:[/bold green] {query}")

    started = perf_counter()
    result = workflow.run(state)
    latency = perf_counter() - started

    # Calculate total tokens and cost across all agent steps
    total_cost = sum(
        float(res.metadata.get("cost_usd", 0.0) or 0.0) for res in result.agent_results
    )
    total_tokens = sum(
        int(res.metadata.get("input_tokens", 0) or 0)
        + int(res.metadata.get("output_tokens", 0) or 0)
        for res in result.agent_results
    )

    # Display Route History
    routes_str = " -> ".join(result.route_history)
    console.print(
        Panel.fit(
            f"[bold yellow]{routes_str}[/bold yellow]",
            title="Workflow Route History",
            border_style="yellow",
        )
    )

    # Display Sources
    if result.sources:
        source_table = Table(
            title="Retrieved Sources", show_header=True, header_style="bold magenta"
        )
        source_table.add_column("#", width=4)
        source_table.add_column("Title", style="bold")
        source_table.add_column("URL")
        for i, src in enumerate(result.sources):
            source_table.add_row(str(i + 1), src.title, src.url or "N/A")
        console.print(source_table)

    # Display Final Answer
    console.print(
        Panel(
            result.final_answer or "No answer produced",
            title="Multi-Agent Final Synthesis",
            border_style="green",
        )
    )

    console.print(
        f"[bold green]Completed in {latency:.2f}s[/bold green] | "
        f"Total Steps: {result.iteration} | "
        f"Total Tokens: {total_tokens} | "
        f"Estimated Cost: ${total_cost:.6f}"
    )


if __name__ == "__main__":
    app()
