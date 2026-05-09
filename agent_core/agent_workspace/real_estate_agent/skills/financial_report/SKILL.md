---
name: synthesize-real-estate-report
description: Tổng hợp phân tích doanh nghiệp Bất động sản. Tập trung vào Hàng tồn kho, Người mua trả tiền trước và cơ cấu nợ.
tools: [mcp_backend_search_financial_reports_ask_vector_post, mcp_backend_query_knowledge_graph_ask_graph_post, web_search, python_interpreter]
---

# Kỹ năng Tổng hợp Báo cáo Phân tích Bất động sản (Real Estate Synthesis)

## KHÓA SINH TỬ (CRITICAL LOCKS)
1. **DÒNG TIỀN LÀ MÁU**: Phải đặc biệt chú ý đến mục "Người mua trả tiền trước" (Advances from customers) vì đây là doanh thu tương lai.
2. **KỶ LUẬT ĐỊNH LƯỢNG**: BẮT BUỘC dùng `python_interpreter` và thư viện chuẩn `fin_lib` để tính toán. Trích xuất số liệu thô và gọi `fin_lib.calculate_real_estate_metrics(data)`.
3. **GIỚI HẠN NGHIÊM NGẶT**: Chỉ được gọi `python_interpreter` TỐI ĐA 2 LẦN.
4. **TIÊU ĐỀ LÀ KẾT LUẬN**: Tiêu đề phải nêu bật được trạng thái dự án hoặc sức khỏe tài chính.

## Procedures

### 1. Truy vấn Vector (Keyword Bank)
Sử dụng các từ khóa sau để lấy bảng số liệu BĐS:

| Nhóm dữ liệu | Từ khóa chiến thuật |
|---|---|
| **Hàng tồn kho** | `Hàng tồn kho`, `Chi phí sản xuất kinh doanh dở dang`, `Chi tiết dự án` |
| **Người mua trả trước** | `Người mua trả tiền trước ngắn hạn`, `Doanh thu chưa thực hiện` |
| **Nợ vay** | `Vay và nợ thuê tài chính`, `Trái phiếu doanh nghiệp` |
| **Dòng tiền** | `Lưu chuyển tiền tệ từ hoạt động kinh doanh` |

### 2. Phân tích & Tính toán
Sử dụng `fin_lib` để tính toán các chỉ số sức khỏe:

**Cách dùng:**
```python
data = {
    "inventory": 5000000,
    "advances_from_customers": 2000000,
    "total_debt": 3000000,
    "equity": 4000000,
    "total_assets": 10000000,
    "revenue": 1000000,
    "gross_profit": 300000
}
print(fin_lib.calculate_real_estate_metrics(data))
```

### 3. Tổng hợp Báo cáo
Sử dụng Template chuyên gia BĐS:

---
# [TÊN CÔNG TY] ([MÃ CK]): PHÂN TÍCH QUY MÔ DỰ ÁN & SỨC KHỎE TÀI CHÍNH [QUÝ/NĂM]

## [TIÊU ĐỀ LUẬN ĐIỂM TỔNG QUÁT]

| Chỉ tiêu Scorecard | Giá trị | Nhận định |
|---|---:|---|
| **Debt/Equity** | [X] | [An toàn/Rủi ro] |
| **Presales Coverage** | [Y]% | [Hấp dẫn/Chậm] |
| **Gross Margin** | [Z]% | [Biên cao/Thấp] |
| **Tỷ trọng Tồn kho** | [A]% | [Tập trung dự án/Đọng vốn] |

### 1) Triển vọng dự án & Hàng tồn kho: [Ví dụ: Dự án [A] sẵn sàng bàn giao trong 2025]
[Phân tích chi tiết hàng tồn kho tập trung ở đâu, tiến độ pháp lý nếu có].

### 2) Sức khỏe tài chính & Áp lực nợ vay: [Ví dụ: Tỷ lệ đòn bẩy duy trì ở mức an toàn]
[Phân tích cơ cấu nợ, trái phiếu và khả năng trả lãi].

### 3) Phân tích Dòng tiền & Điểm rơi lợi nhuận: [Ví dụ: Người mua trả trước tăng mạnh, tín hiệu tích cực]
[Phân tích dòng tiền từ HĐKD và mục người mua trả trước].

### 4) Luận điểm đầu tư & Rủi ro
- **Luận điểm:** [1 dòng].
- **Rủi ro:** [Pháp lý, Lãi suất, Tiến độ bàn giao].
---
