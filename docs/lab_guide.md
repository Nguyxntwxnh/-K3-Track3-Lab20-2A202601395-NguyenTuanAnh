# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

✅ Đã hoàn thành call LLM đơn lẻ end-to-end đo lường latency và chi phí token.

## Milestone 2: Supervisor

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

✅ Đã hoàn thành routing policy theo trạng thái dữ liệu (sources -> analyst_notes -> final_answer -> done) và guardrail `max_iterations=6`.

## Milestone 3: Worker agents

- `src/multi_agent_research_lab/agents/researcher.py`
- `src/multi_agent_research_lab/agents/analyst.py`
- `src/multi_agent_research_lab/agents/writer.py`

✅ Đã hoàn thành các worker agents với nhiệm vụ phân tách rõ ràng và tích hợp handoff qua `ResearchState`.

## Milestone 4: Trace và benchmark

- `src/multi_agent_research_lab/observability/tracing.py`
- `src/multi_agent_research_lab/evaluation/benchmark.py`
- `src/multi_agent_research_lab/evaluation/report.py`

Benchmark thu được:

| Metric | Single-Agent Baseline | Multi-Agent (LangGraph) |
|---|---|---|
| Latency | ~4.86s - 5.96s | ~15.77s - 18.63s |
| Cost (USD) | $0.000081 | $0.000279 |
| Quality Score | 6.5 / 10 | 9.3 / 10 |
| Citation Coverage | 0% (không có nguồn rời) | 100% (trích dẫn đầy đủ [1], [2], [3]) |
| Failure Rate | 0% | 0% |

---

## Exit Ticket

### 1. Case nào NÊN dùng multi-agent? Vì sao?
- **Trường hợp áp dụng**: Các bài toán phức tạp đòi hỏi nhiều bước xử lý chuyên biệt (như tổng hợp báo cáo nghiên cứu sâu, phân tích dữ liệu đa nguồn kết hợp viết báo cáo, hệ thống hỗ trợ kỹ thuật đa tầng, hoặc tự động hóa quy trình nghiệp vụ dài).
- **Lý do dựa trên số liệu thực nghiệm**: 
  - **Tránh loãng ngữ cảnh (Context Dilution)**: Mỗi agent chỉ tập trung vào một prompt và một nhiệm vụ duy nhất (Researcher chỉ tìm nguồn, Analyst chỉ phản biện, Writer chỉ tổng hợp văn phong).
  - **Chất lượng và Độ chính xác cao hơn vượt trội**: Điểm chất lượng tăng từ **6.5 lên 9.3**, độ phủ trích dẫn đạt **100%**, loại bỏ tình trạng hallucination do nguồn được kiểm chứng qua nhiều bước.
  - **Khả năng quan sát (Observability)**: Dễ dàng debug từng mắt xích thông qua LangSmith trace thay vì một black-box LLM call.

### 2. Case nào KHÔNG NÊN dùng multi-agent? Vì sao?
- **Trường hợp áp dụng**: Các tác vụ đơn giản, câu hỏi tra cứu thông tin nhanh (FAQ, tóm tắt đoạn văn ngắn, phân loại cảm xúc văn bản, dịch thuật trực tiếp, hoặc các chatbot phản hồi tức thì với người dùng).
- **Lý do dựa trên số liệu thực nghiệm**:
  - **Độ trễ cao (High Latency)**: Multi-agent qua 4 bước mất tới **~18.6s** so với chỉ **~4.8s** của Single-agent (chậm hơn gấp 3 - 4 lần).
  - **Chi phí Token cao (Cost)**: Tiêu tốn nhiều lượt gọi API trung gian (tốn gấp ~3.5 lần token).
  - **Độ phức tạp kỹ thuật không cần thiết**: Nguy cơ gặp lỗi điều phối, vòng lặp vô hạn hoặc thất bại mạng nếu hệ thống không có bài toán đủ phức tạp để bù đắp chi phí vận hành.
