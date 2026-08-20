# Design Document: Multi-Agent Research System

## Problem

Xây dựng hệ thống trợ lý nghiên cứu tự động (**Autonomous Research Assistant**) có khả năng nhận các câu hỏi nghiên cứu kỹ thuật chuyên sâu, tìm kiếm và chọn lọc nguồn tài liệu tin cậy, thực hiện phân tích phản biện kỹ thuật, và tổng hợp thành bản báo cáo hoàn chỉnh có trích dẫn nguồn minh bạch.

## Why multi-agent?

Mô hình **Single-Agent** ("một agent làm tất cả") thường gặp các vấn đề lớn khi xử lý các bài toán phức tạp:
1. **Loãng ngữ cảnh (Context Dilution)**: Một prompt đơn lẻ gánh cả việc tìm kiếm, phân tích và định dạng báo cáo sẽ dễ bỏ sót chi tiết hoặc bị phân tâm bởi các thông tin nhiễu.
2. **Nguy cơ Hallucination cao**: Không có cơ chế kiểm tra chéo độc lập giữa dữ liệu tìm được và lập luận đưa ra.
3. **Khó Debug**: Khi kết quả sai, rất khó xác định lỗi nằm ở bước tìm kiếm hay bước lập luận tổng hợp.

Hệ thống **Multi-Agent** phân rã bài toán thành các vai trò chuyên biệt, truyền dữ liệu qua một **Shared State** minh bạch và được điều phối bởi **Supervisor Router**.

## Agent Roles

| Agent | Responsibility | Input | Output | Failure Mode & Mitigation |
|---|---|---|---|---|
| **Supervisor** | Điều phối luồng làm việc, quyết định agent tiếp theo và kiểm soát dừng | `ResearchState` | Route (`researcher`, `analyst`, `writer`, `done`) | Vòng lặp vô hạn $\rightarrow$ Guardrail `max_iterations=6` |
| **Researcher** | Tìm kiếm thông tin liên quan và trích xuất nguồn dữ liệu | `state.request.query`, `max_sources` | `state.sources`, `state.research_notes` | Không tìm thấy nguồn $\rightarrow$ Mock search fallback thông minh |
| **Analyst** | Phản biện, so sánh các góc nhìn kỹ thuật và đánh giá độ tin cậy | `state.research_notes` | `state.analysis_notes` | Thiếu dữ liệu $\rightarrow$ Báo cáo thiếu sót thay vì suy đoán sai |
| **Writer** | Tổng hợp báo cáo cuối cùng với văn phong chuẩn mực và trích dẫn | `state.research_notes`, `state.analysis_notes`, `state.sources` | `state.final_answer` | Quên trích dẫn $\rightarrow$ Prompt cấu trúc yêu cầu bắt buộc định dạng `[i]` |

## Shared State (`ResearchState`)

- `request`: Đối tượng `ResearchQuery` chứa câu hỏi gốc, độ dài, đối tượng độc giả.
- `iteration`: Bộ đếm số bước thực thi (dùng cho guardrail).
- `route_history`: Lưu vết toàn bộ chuỗi điều phối của supervisor.
- `sources`: Danh sách `SourceDocument` thu thập được từ SearchClient.
- `research_notes`: Ghi chú tóm tắt dữ liệu thô từ Researcher.
- `analysis_notes`: Ghi chú phân tích phản biện từ Analyst.
- `final_answer`: Văn bản tổng hợp cuối cùng của Writer.
- `agent_results`: Danh sách kết quả chi tiết từng agent kèm token, chi phí và thời gian.
- `trace`: Lịch sử sự kiện đo đạc để phục vụ debug và observability.

## Routing Policy

Đồ thị trạng thái LangGraph (`StateGraph`):
```text
[START] -> supervisor
              |---> (chưa có sources)        -> researcher -> supervisor
              |---> (chưa có analysis_notes) -> analyst    -> supervisor
              |---> (chưa có final_answer)   -> writer     -> supervisor
              |---> (đã xong / max_iter)     -> [END]
```

## Guardrails

- **Max iterations**: 6 bước (ngăn chặn vòng lặp vô tận giữa supervisor và workers).
- **Timeout**: 60 giây cho mỗi lượt gọi API.
- **Retry**: Áp dụng Exponential Backoff (`tenacity`) tối đa 3 lần cho các lỗi mạng / RateLimit.
- **Fallback**: Tự động chuyển đổi sang Mock / Offline Generation khi gặp lỗi kết nối hoặc hết quota API.
- **Validation**: Pydantic Schema kiểm tra tính toàn vẹn của dữ liệu tại các điểm handoff.

## Benchmark Plan

- **Queries thử nghiệm**:
  1. *"Research GraphRAG state-of-the-art and write a 500-word summary"*
  2. *"Compare single-agent and multi-agent workflows for customer support"*
  3. *"Summarize production guardrails for LLM agents"*
- **Metrics đo lường**:
  - Wall-clock Latency (giây).
  - Estimated Cost (USD) / Token Usage.
  - Quality Score (Thang điểm 0 - 10).
  - Citation Coverage (Tỉ lệ % luận điểm có nguồn trích dẫn).
  - Failure Rate (Tỉ lệ phiên chạy lỗi).
