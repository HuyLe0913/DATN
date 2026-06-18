---
name: synthesize-banking-report
description: Tổng hợp phân tích Ngân hàng thành báo cáo chuyên gia hoàn chỉnh. Đúc kết văn phong chuyên viên tài chính, khắt khe trong đối chiếu số liệu.
tools: [mcp_backend_search_financial_reports_ask_vector_post, mcp_backend_query_knowledge_graph_ask_graph_post, web_search, python_interpreter]
---

# Kỹ năng Tổng hợp Báo cáo Phân tích Ngân hàng (High-Precision Synthesis)

## KHÓA SINH TỬ (CRITICAL LOCKS)
1. **KIÊN QUYẾT TỰ LẬP**: TUYỆT ĐỐI KHÔNG ĐƯỢC hỏi người dùng "có muốn làm tiếp không". Phải chủ động truy vấn Vector để lấy đủ số liệu (BCTC, Nợ xấu, CASA, NIM). KIỂM TRA KỸ ngữ cảnh đã có trước khi gọi thêm công cụ để tránh trùng lặp.
2. **NGHIÊM CẤM DẤU CHẤM HỎI (?)**: Báo cáo chuyên gia không được có dấu `?`. Nếu chưa rõ số, hãy tính toán hoặc ghi "Ước tính".
3. **TIÊU ĐỀ LÀ KẾT LUẬN**: Tiêu đề các mục phải tóm tắt luôn nội dung đoạn đó (Ví dụ: `### 2) Chất lượng tài sản: Nợ xấu có dấu hiệu đạt đỉnh, bộ đệm dự phòng vững chắc`).
4. **KỶ LUẬT ĐỊNH LƯỢNG**: BẮT BUỘC dùng `python_interpreter` và thư viện chuẩn `fin_lib` để tính toán. TUYỆT ĐỐI KHÔNG tự viết công thức toán học. Bạn phải trích xuất số liệu thô vào một dictionary và gọi `fin_lib.calculate_banking_metrics(data)`.
5. **GIỚI HẠN NGHIÊM NGẶT**: Chỉ được gọi `python_interpreter` TỐI ĐA 2 LẦN. Hãy gộp tất cả các phép tính vào 1-2 lượt gọi này.
6. **CHỐNG LẶP (ANTI-LOOP)**: Nếu kết quả trả về từ Vector Search đã chứa bảng số liệu bạn cần, hãy TIẾN HÀNH PHÂN TÍCH NGAY.
7. **ĐIỀU HƯỚNG GRAPH VS VECTOR (HYBRID ROUTING)**: 
   - Ưu tiên dùng **Vector Search (`ask_vector`)** khi cần BẢNG SỐ LIỆU CHI TIẾT của 1 ngân hàng (Cân đối kế toán, P&L, Thuyết minh chi tiết).
   - BẮT BUỘC dùng **GraphRAG (`query_knowledge_graph`)** khi câu hỏi yêu cầu phân tích **Sự kiện (Events)**, **Tác động chéo**, **Giải trình biến động**, hoặc so sánh/tìm **Mối liên hệ giữa NHIỀU thực thể cùng lúc** (VD: "Sự kiện nào giải trình biến động thu nhập lãi thuần của các ngân hàng?").

## Procedures

### 1. Truy vấn Vector toàn diện (Keyword-First Strategy)
Hệ thống đã được tối ưu cho **BM25 (Keyword matching)**. Bạn PHẢI sử dụng chính xác các danh từ chuyên môn tiếng Việt sau đây để lấy bảng số liệu:

| Nhóm dữ liệu | Từ khóa chiến thuật (BẮT BUỘC) | Tham số `limit` |
|---|---|---|
| **Bảng Cân đối** | `BẢNG CÂN ĐỐI KẾ TOÁN HỢP NHẤT` | 3 |
| **Quy mô Tài sản** | `TỔNG CỘNG TÀI SẢN` | 2 |
| **P&L (Kết quả KD)** | `BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH HỢP NHẤT` | 3 |
| **Chi tiết NIM** | `Thu nhập lãi thuần` | 2 |
| **Chất lượng nợ** | `Phân loại nợ` | 2 |

- **CHIẾN THUẬT QUY ĐỊNH:**
  ### 1) KEYWORD BANK (ĐỘ CHÍNH XÁC CAO):
- **BCTC Chính**: `Mẫu B02 Báo cáo tình hình tài chính hợp nhất`, `Mẫu B03 Báo cáo kết quả hoạt động hợp nhất`.
- **CASA (Tiền gửi)**: `Mẫu B05 Thuyết minh Tiền gửi của khách hàng phân theo loại hình`.
- **Nợ xấu (NPL)**: `Mẫu B05 Thuyết minh Phân loại nợ cho vay khách hàng`, `Nợ nhóm 3 nhóm 4 nhóm 5`.
- **NIM & Lãi suất**: `Mẫu B05 Thuyết minh Thu nhập lãi và các khoản thu nhập tương tự`, `Kỳ định lại lãi suất`.
- **Dự phòng**: `Dự phòng rủi ro cho vay khách hàng`.

### 2) PROCEDURES
- **Lượt 1 (Data Gathering)**: Ưu tiên lấy 3 bảng summary (Cân đối B02, Kết quả KD B03, Phân loại nợ B05). Sử dụng `limit=3` để đảm bảo lấy được trang chủ báo cáo.
- **Lượt 2 (Analysis & Calculation)**: Sau khi có số liệu, dùng `python_interpreter` để tính toán ngay các chỉ số:
  - `NPL Ratio = (Nợ nhóm 3+4+5) / Tổng dư nợ`
  - `CASA Ratio = Tiền gửi không kỳ hạn / Tổng tiền gửi khách hàng`
  - `NIM = Thu nhập lãi thuần / Tài sản có sinh lãi bình quân`
- **Lượt 3 (Synthesis)**: Tổng hợp báo cáo theo template. Chỉ tìm thêm (Lượt 2.5) nếu thực sự thiếu số liệu trọng yếu.

### 2. Phân tích & Tính toán (Calculation Phase)
Bạn PHẢI sử dụng `fin_lib` để tính toán. 

**Cách dùng ví dụ:**
```python
data = {
    "nPL_group3": 1500000, "nPL_group4": 500000, "nPL_group5": 2000000,
    "total_loans": 500000000,
    "demand_deposits": 120000000, "total_deposits": 400000000,
    "net_interest_income": 15000000, "avg_earning_assets": 450000000,
    "operating_expenses": 5000000, "total_operating_income": 20000000,
    "loan_loss_reserve": 4500000
}
print(fin_lib.calculate_banking_metrics(data))
```

### 3. Tổng hợp Báo cáo (Synthesis Phase)
Sử dụng Template chuyên gia dưới đây:

---
# [TÊN NGÂN HÀNG] ([MÃ CK]): PHÂN TÍCH QUY MÔ & HIỆU QUẢ [QUÝ/NĂM]

## [TIÊU ĐỀ LUẬN ĐIỂM TỔNG QUÁT TRÊN 1 DÒNG]

| Chỉ tiêu Scorecard | Giá trị | Nhận định |
|---|---:|---|
| **NIM** | [X] bps | [Tăng/Giảm] |
| **ROE** | [Y]% | [Cải thiện/Sụt giảm] |
| **CASA** | [Z]% | [Điểm sáng/Rủi ro] |
| **NPL (Nợ xấu)** | [A]% | [Kiểm soát tốt/Cần theo dõi] |

### 1) Điểm nhấn KQKD: [Ví dụ: Thu nhập lãi thuần bứt phá nhờ tín dụng tăng tốc]
[Đoạn văn phân tích sâu 4-5 câu về driver lợi nhuận].

### 2) Chất lượng tài sản: [Ví dụ: Áp lực nợ xấu hạ nhiệt, lớp áo giáp dự phòng dày]
[Phân tích về NPL, LLR và xu hướng nợ nhóm 2].

### 3) Hiệu quả vận hành & Sinh lời: [Ví dụ: NIM cải thiện rõ rệt nhờ chi phí vốn rẻ]
[Phân tích về CIR, NIM, ROE].

### 4) Luận điểm đầu tư & Rủi ro
- **Luận điểm:** [1 dòng in đậm].
- **Rủi ro:** [Nêu 1-2 rủi ro chính].
---
