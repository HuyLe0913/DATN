---
name: synthesize-securities-report
description: Tổng hợp phân tích Công ty Chứng khoán. Tập trung vào cho vay Margin, tự doanh và thị phần môi giới.
tools: [mcp_backend_search_financial_reports_ask_vector_post, mcp_backend_query_knowledge_graph_ask_graph_post, web_search, python_interpreter]
---

# Kỹ năng Tổng hợp Báo cáo Phân tích Chứng khoán (Securities Synthesis)

## KHÓA SINH TỬ (CRITICAL LOCKS)
1. **DƯ NỢ MARGIN**: Đây là động lực tăng trưởng chính. Phải tìm chính xác mục "Cho vay hoạt động ký quỹ".
2. **HIỆU QUẢ TỰ DOANH**: Phải đối chiếu lãi/lỗ từ FVTPL và HTM.
3. **KỶ LUẬT ĐỊNH LƯỢNG**: BẮT BUỘC dùng `python_interpreter` và thư viện chuẩn `fin_lib` để tính toán. Gọi `fin_lib.calculate_securities_metrics(data)`.
4. **ĐIỀU HƯỚNG GRAPH VS VECTOR (HYBRID ROUTING)**: 
   - Ưu tiên dùng **Vector Search (`ask_vector`)** khi cần BẢNG SỐ LIỆU CHI TIẾT của 1 công ty.
   - BẮT BUỘC dùng **GraphRAG (`query_knowledge_graph`)** khi câu hỏi yêu cầu phân tích **Sự kiện (Events)**, **Tác động chéo**, **Giải trình biến động**, hoặc so sánh/tìm **Mối liên hệ giữa NHIỀU thực thể cùng lúc**.

## Procedures

### 1. Truy vấn Vector (Keyword Bank)
Sử dụng các từ khóa sau để lấy bảng số liệu Chứng khoán:

| Nhóm dữ liệu | Từ khóa chiến thuật |
|---|---|
| **Cho vay (Margin)** | `Các khoản cho vay`, `Cho vay hoạt động ký quỹ`, `Margin` |
| **Tự doanh** | `Tài sản tài chính ghi nhận thông qua lãi/lỗ (FVTPL)`, `Chứng khoán sẵn sàng để bán (AFS)` |
| **Doanh thu nghiệp vụ** | `Doanh thu nghiệp vụ môi giới`, `Doanh thu nghiệp vụ bảo lãnh` |
| **Phí môi giới** | `Chi phí nghiệp vụ môi giới` |

### 2. Phân tích & Tính toán
Sử dụng `fin_lib` để tính toán:

**Cách dùng:**
```python
data = {
    "margin_loans": 10000000,
    "equity": 5000000,
    "brokerage_revenue": 500000,
    "brokerage_expenses": 300000,
    "fvtpl_gains": 200000,
    "fvtpl_losses": 50000
}
print(fin_lib.calculate_securities_metrics(data))
```

### 3. Tổng hợp Báo cáo
Sử dụng Template chuyên gia Chứng khoán:

---
# [TÊN CÔNG TY] ([MÃ CK]): HIỆU QUẢ TỰ DOANH & THỊ PHẦN MÔI GIỚI [QUÝ/NĂM]

## [TIÊU ĐỀ LUẬN ĐIỂM TỔNG QUÁT]

| Chỉ tiêu Scorecard | Giá trị | Nhận định |
|---|---:|---|
| **Margin/Equity** | [X] | [An toàn/Kịch trần] |
| **Biên LN Môi giới** | [Y]% | [Cạnh tranh/Cải thiện] |
| **FVTPL Net** | [Z] tỷ | [Lãi lớn/Lỗ] |
| **Tỷ trọng Margin** | [A]% | [Phụ thuộc/Đa dạng] |

### 1) Hoạt động Cho vay (Margin): [Ví dụ: Dư nợ Margin lập đỉnh, đóng góp chính vào doanh thu]
[Phân tích dư nợ margin, xu hướng so với quý trước].

### 2) Danh mục Tự doanh: [Ví dụ: FVTPL khởi sắc nhờ nắm giữ các cổ phiếu Bluechip]
[Chi tiết các mã cổ phiếu/trái phiếu đang nắm giữ trong danh mục FVTPL, AFS].

### 3) Môi giới & Thị phần: [Ví dụ: Áp lực cạnh tranh phí 0đ làm thu hẹp biên lợi nhuận]
[Phân tích doanh thu, chi phí môi giới và thị phần nếu có dữ liệu].

### 4) Luận điểm đầu tư & Rủi ro
- **Luận điểm:** [1 dòng].
- **Rủi ro:** [Thị trường sụt giảm, Lãi suất vay tăng, Cạnh tranh phí].
---
