---
name: synthesize-insurance-report
description: Tổng hợp phân tích doanh nghiệp Bảo hiểm. Tập trung vào lợi nhuận nghiệp vụ và danh mục đầu tư tài chính.
tools: [mcp_backend_search_financial_reports_ask_vector_post, mcp_backend_query_knowledge_graph_ask_graph_post, web_search, python_interpreter]
---

# Kỹ năng Tổng hợp Báo cáo Phân tích Bảo hiểm (Insurance Synthesis)

## KHÓA SINH TỬ (CRITICAL LOCKS)
1. **LỢI NHUẬN TÀI CHÍNH**: Các công ty bảo hiểm sống nhờ đầu tư tiền phí. Phải tìm mục "Doanh thu hoạt động tài chính".
2. **KỶ LUẬT ĐỊNH LƯỢNG**: BẮT BUỘC dùng `python_interpreter` và thư viện chuẩn `fin_lib` để tính toán.
3. **KẾT QUẢ NGHIỆP VỤ**: Đối chiếu Doanh thu phí bảo hiểm thuần và Chi bồi thường.
4. **ĐIỀU HƯỚNG GRAPH VS VECTOR (HYBRID ROUTING)**: 
   - Ưu tiên dùng **Vector Search (`ask_vector`)** khi cần BẢNG SỐ LIỆU CHI TIẾT của 1 công ty.
   - BẮT BUỘC dùng **GraphRAG (`query_knowledge_graph`)** khi câu hỏi yêu cầu phân tích **Sự kiện (Events)**, **Tác động chéo**, **Giải trình biến động**, hoặc so sánh/tìm **Mối liên hệ giữa NHIỀU thực thể cùng lúc**.

## Procedures

### 1. Truy vấn Vector (Keyword Bank)
Sử dụng các từ khóa sau:

| Nhóm dữ liệu | Từ khóa chiến thuật |
|---|---|
| **Nghiệp vụ** | `Doanh thu thuần hoạt động kinh doanh bảo hiểm`, `Chi bồi thường bảo hiểm`, `Dự phòng nghiệp vụ` |
| **Đầu tư** | `Tiền gửi ngắn hạn`, `Chứng khoán đầu tư`, `Doanh thu hoạt động tài chính` |
| **P&L** | `Lợi nhuận trước thuế`, `Chi phí quản lý doanh nghiệp` |

### 2. Phân tích & Tính toán
Sử dụng `fin_lib` (Dùng chung bộ `general_metrics` hoặc bộ riêng nếu có).

### 3. Tổng hợp Báo cáo
Sử dụng Template chuyên gia Bảo hiểm:

---
# [TÊN CÔNG TY] ([MÃ CK]): HIỆU QUẢ ĐẦU TƯ & KẾT QUẢ NGHIỆP VỤ [QUÝ/NĂM]

## [TIÊU ĐỀ LUẬN ĐIỂM TỔNG QUÁT]

| Chỉ tiêu Scorecard | Giá trị | Nhận định |
|---|---:|---|
| **Lợi nhuận Đầu tư** | [X] tỷ | [Tăng/Giảm] |
| **ROE** | [Y]% | [Cải thiện/Sụt giảm] |
| **Combined Ratio** | [Z]% | [Tốt/Kém] |
| **Tỷ trọng Tiền gửi** | [A]% | [An toàn/Đang chuyển dịch] |

### 1) Hoạt động Kinh doanh Bảo hiểm: [Ví dụ: Doanh thu phí bảo hiểm thuần duy trì đà tăng trưởng]
[Phân tích doanh thu phí, tỷ lệ bồi thường và dự phòng nghiệp vụ].

### 2) Danh mục Đầu tư Tài chính: [Ví dụ: Hưởng lợi từ môi trường lãi suất tiền gửi cao]
[Chi tiết cơ cấu danh mục đầu tư: tiền gửi, trái phiếu, cổ phiếu].

### 3) Hiệu quả Vận hành: [Ví dụ: Tối ưu hóa chi phí quản lý giúp bảo toàn lợi nhuận]
[Phân tích chi phí bán hàng, chi phí quản lý và lợi nhuận ròng].

### 4) Luận điểm đầu tư & Rủi ro
- **Luận điểm:** [1 dòng].
- **Rủi ro:** [Lãi suất giảm, Thiên tai/Sự kiện bồi thường lớn, Cạnh tranh phí].
---
