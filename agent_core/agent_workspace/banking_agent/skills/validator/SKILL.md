---
name: internal_validator
description: Tự kiểm tra và phản biện dữ liệu trong báo cáo để tránh ảo tưởng (hallucination).
tools: [search_hybrid, python_interpreter]
---

# Internal Report Validator

Kỹ năng này hoạt động như một lớp lọc cuối cùng để đảm bảo mọi thông tin trong báo cáo tài chính là chính xác, có cơ sở và logic.

## Procedures

### 1. Đối soát con số (Figure Verification)
- Với mỗi số liệu tài chính quan trọng (Doanh thu, Lợi nhuận, Nợ), thực hiện truy vấn lại `search_hybrid` để xác nhận số đó có tồn tại trong tài liệu gốc hay không.
- Nếu phát hiện sai số, yêu cầu Agent chỉnh sửa lại dựa trên trích dẫn chính xác.

### 2. Kiểm tra tính nhất quán (Consistency Check)
- Đảm bảo rằng các số liệu ở các phần khác nhau của báo cáo không mâu thuẫn (ví dụ: Tổng tài sản phải bằng Tổng nguồn vốn).
- Sử dụng `python_interpreter` để tính toán lại các tổng số nếu cần.

### 3. Kiểm chứng trích dẫn (Source Check)
- Kiểm tra xem các trích dẫn (ví dụ: "[Trang 10, BCTC]") có thực sự dẫn đến nội dung tương ứng không.

### 4. Đánh giá tính khách quan (Bias Check)
- Đảm bảo báo cáo không chỉ đưa ra các tin tích cực mà phải bao gồm cả các rủi ro và mặt hạn chế đã tìm thấy trong phần Thuyết minh báo cáo.

## Guidelines for Validation
- Nếu tỷ lệ sai sót > 10%, yêu cầu hủy bản thảo và thực hiện lại giai đoạn Research.
- Luôn giữ thái độ "hoài nghi lành mạnh" đối với các kết luận của bước Synthesis trước đó.
