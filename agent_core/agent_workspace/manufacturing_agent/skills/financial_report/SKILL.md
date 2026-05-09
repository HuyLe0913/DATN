---
name: synthesize-manufacturing-report
description: Tổng hợp phân tích doanh nghiệp Sản xuất, Bán lẻ và Dịch vụ (Chung). Tập trung vào biên lợi nhuận, ROE và tính thanh khoản.
tools: [mcp_backend_search_financial_reports_ask_vector_post, mcp_backend_query_knowledge_graph_ask_graph_post, web_search, python_interpreter]
---

# Kỹ năng Tổng hợp Báo cáo Phân tích Doanh nghiệp Sản xuất/Bán lẻ (General Industry)

## KHÓA SINH TỬ (CRITICAL LOCKS)
1. **BIÊN LỢI NHUẬN GỘP**: Phải đối chiếu với quý trước để thấy xu hướng giá vốn.
2. **KỶ LUẬT ĐỊNH LƯỢNG**: BẮT BUỘC dùng `python_interpreter` và thư viện chuẩn `fin_lib` để tính toán. Gọi `fin_lib.calculate_general_metrics(data)`.
3. **GIỚI HẠN NGHIÊM NGẶT**: Chỉ được gọi `python_interpreter` TỐI ĐA 2 LẦN.

## Procedures

### 1. Truy vấn Vector (Keyword Bank)
Sử dụng các từ khóa sau:

| Nhóm dữ liệu | Từ khóa chiến thuật |
|---|---|
| **KQKD** | `Doanh thu thuần`, `Giá vốn hàng bán`, `Lợi nhuận gộp` |
| **Chi phí** | `Chi phí bán hàng`, `Chi phí quản lý doanh nghiệp` |
| **Thanh khoản** | `Tài sản ngắn hạn`, `Nợ ngắn hạn` |
| **Hiệu quả** | `Lợi nhuận sau thuế của công ty mẹ` |

### 2. Phân tích & Tính toán
Sử dụng `fin_lib` để tính toán:

**Cách dùng:**
```python
data = {
    "revenue": 1000000,
    "gross_profit": 300000,
    "net_profit": 100000,
    "equity": 800000,
    "current_assets": 500000,
    "current_liabilities": 300000
}
print(fin_lib.calculate_general_metrics(data))
```

### 3. Tổng hợp Báo cáo
Sử dụng Template chung:

---
# [TÊN CÔNG TY] ([MÃ CK]): PHÂN TÍCH HIỆU QUẢ VẬN HÀNH [QUÝ/NĂM]

## [TIÊU ĐỀ LUẬN ĐIỂM TỔNG QUÁT]

| Chỉ tiêu Scorecard | Giá trị | Nhận định |
|---|---:|---|
| **Gross Margin** | [X]% | [Tăng/Giảm] |
| **ROE** | [Y]% | [Cải thiện/Sụt giảm] |
| **Current Ratio** | [Z] | [An toàn/Rủi ro] |
| **Net Margin** | [A]% | [Duy trì/Biến động] |

### 1) Kết quả Kinh doanh & Biên lợi nhuận: [Ví dụ: Biên lợi nhuận gộp cải thiện nhờ tối ưu giá vốn]
[Phân tích doanh thu, tăng trưởng và các yếu tố ảnh hưởng đến biên lợi nhuận].

### 2) Hiệu quả Quản lý chi phí: [Ví dụ: Chi phí bán hàng tăng mạnh do mở rộng thị phần]
[Phân tích chi phí SG&A và tác động đến lợi nhuận ròng].

### 3) Sức khỏe Tài chính & Thanh khoản: [Ví dụ: Cơ cấu tài chính vững mạnh, tiền mặt dồi dào]
[Phân tích nợ vay, tỷ lệ thanh toán và vòng quay vốn lưu động].

### 4) Luận điểm đầu tư & Rủi ro
- **Luận điểm:** [1 dòng].
- **Rủi ro:** [Giá nguyên liệu tăng, Cạnh tranh gay gắt, Sụt giảm nhu cầu].
---
