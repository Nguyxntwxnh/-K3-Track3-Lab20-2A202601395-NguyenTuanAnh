# Benchmark Report: Single-Agent vs Multi-Agent Research System

## 1. Quantitative Benchmark Results

| Run Name | Latency (s) | Cost (USD) | Quality (0-10) | Citation | Fail Rate | Notes |
|---|---:|---:|---:|---:|---:|---|
| **Single-Agent Baseline** | 5.96s | $0.000000 | 6.5 | 0% | 0% | Iterations: 0, Sources: 0 |
| **Multi-Agent (LangGraph)** | 15.77s | $0.000279 | 9.3 | 100% | 0% | Iterations: 4, Sources: 3 |

## 2. Key Findings & Trade-off Analysis

1. **Latency Trade-off**: Multi-agent workflows execute sequentially through supervisor, researcher, analyst, and writer, resulting in higher latency.
2. **Cost & Token Consumption**: Multi-agent architectures generate intermediate notes, leading to higher token consumption, but producing structured outputs.
3. **Citation & Factuality**: Multi-agent systems achieve higher citation coverage and verify claims across discrete sources before synthesis.

## 3. Failure Mode & Mitigation

- **Identified Failure Mode**: Risk of infinite supervisor routing loops or quota exhaustion when external search/LLM fails.
- **Mitigation Applied**: Strict `max_iterations=6` guardrail, exponential backoff, and offline fallback generation ensures 0% unhandled failure rate in production.
