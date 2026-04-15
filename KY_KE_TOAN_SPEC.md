# Đặc Tả Chi Tiết Kỳ Kế Toán

## 1. Mục tiêu
Kỳ kế toán là cơ chế chia một năm tài chính thành 12 kỳ theo tháng để kiểm soát việc ghi nhận, chỉnh sửa và khóa dữ liệu kế toán - kho - bán hàng.

## 2. Phạm vi
Kỳ kế toán áp dụng cho các chứng từ phát sinh có ngày nghiệp vụ hoặc ngày hạch toán, gồm:
- Đơn bán hàng
- Hóa đơn bán hàng
- Phiếu thu
- Phiếu trả hàng / đổi trả
- Đơn mua hàng
- Hóa đơn mua vào
- Phiếu chi
- Phiếu nhập kho
- Phiếu xuất kho
- Phiếu kiểm kê
- Phiếu điều chỉnh kiểm kê
- Ghi sổ cái / bút toán tổng hợp

## 3. Cấu trúc dữ liệu
Mỗi kỳ kế toán có các thuộc tính:
- Năm tài chính
- Số kỳ từ 1 đến 12
- Tên kỳ
- Từ ngày
- Đến ngày
- Trạng thái: đang mở / đã khóa
- Ghi chú
- Khóa lúc
- Khóa bởi
- Người tạo
- Ngày tạo, ngày cập nhật

## 4. Quy tắc nghiệp vụ
- Một năm có đúng 12 kỳ theo tháng.
- Khi tạo kỳ cho một năm, hệ thống sinh đủ 12 dòng dữ liệu.
- Kỳ mặc định ở trạng thái đang mở.
- Chứng từ thuộc kỳ đang mở được phép tạo, sửa, xóa và ghi sổ.
- Chứng từ thuộc kỳ đã khóa không được sửa, xóa hoặc ghi sổ lại.
- Nếu kỳ chưa được tạo, hệ thống phải báo lỗi và không cho ghi sổ.
- Việc khóa kỳ chỉ ảnh hưởng đến kỳ đó, không tác động sang kỳ khác.
- Dữ liệu các kỳ đã khóa phải giữ nguyên để đối chiếu báo cáo sau này.

## 5. Luồng sử dụng
### 5.1 Tạo kỳ
- Người dùng vào màn Kỳ kế toán.
- Chọn năm.
- Bấm tạo đủ 12 kỳ.
- Hệ thống sinh 12 kỳ theo từng tháng của năm đó.

### 5.2 Khóa kỳ
- Người dùng chọn một kỳ đang mở.
- Bấm khóa kỳ.
- Hệ thống chuyển trạng thái sang đã khóa.
- Từ thời điểm đó, mọi thao tác sửa/xóa/ghi sổ trên chứng từ thuộc kỳ này bị chặn.

### 5.3 Mở khóa kỳ
- Nếu được cho phép theo phân quyền, người dùng có thể mở lại kỳ đã khóa.
- Sau khi mở lại, chứng từ trong kỳ đó có thể chỉnh sửa tiếp.

## 6. Kiểm soát dữ liệu
Hệ thống phải kiểm tra kỳ kế toán ở 2 mức:
- Mức model: chặn save/delete các chứng từ thuộc kỳ đã khóa.
- Mức ghi sổ: chặn post ledger nếu ngày chứng từ nằm trong kỳ đã khóa.

## 7. Giao diện
Màn hình Kỳ kế toán cần có:
- Bộ lọc theo năm
- Nút tạo đủ 12 kỳ
- Bảng danh sách 12 kỳ
- Hiển thị trạng thái mở/khóa
- Nút khóa/mở khóa từng kỳ
- Hiển thị người khóa, thời điểm khóa và ghi chú

## 8. Báo cáo và đối chiếu
- Số liệu báo cáo sổ cái, tồn kho, doanh thu, công nợ phải đọc theo ngày nằm trong kỳ.
- Khi kỳ đã khóa, báo cáo của kỳ đó được coi là chốt số liệu.
- Chỉnh sửa ở kỳ sau không được làm thay đổi dữ liệu đã chốt của kỳ trước.

## 9. Phân quyền đề xuất
- Admin / kế toán trưởng: tạo kỳ, khóa kỳ, mở khóa kỳ.
- Nhân viên nghiệp vụ: chỉ được thao tác trên kỳ đang mở nếu có quyền phù hợp.

## 10. Ghi chú triển khai
- Kỳ kế toán nên nằm ở hệ thống dùng chung để tất cả phân hệ đọc chung.
- Nên map ngày chứng từ / ngày hạch toán của từng chứng từ vào kỳ tương ứng.
- Khi mở năm mới, có thể tạo trước đủ 12 kỳ và khóa dần theo tháng thực tế.
