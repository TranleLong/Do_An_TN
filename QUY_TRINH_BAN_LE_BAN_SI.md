# Quy trình vận hành ERP: bán lẻ, bán sỉ, kho và kế toán bán hàng

Tài liệu này áp dụng cho hệ thống hiện tại, nơi **nhân viên bán hàng** có thể thao tác luôn các bước xuất kho theo đơn.

---

## 1) Mục tiêu của từng phân hệ

### Kho / kế toán kho
- Quản lý tồn kho theo từng kho và từng hàng hóa.
- Cập nhật giá vốn bình quân khi nhập kho.
- Trừ tồn và ghi nhận giá vốn khi xuất kho.

### Bán hàng / kế toán bán hàng
- Tạo đơn bán theo 3 loại: bán lẻ, bán buôn, bán gara/xưởng.
- Xác nhận đơn là bước chốt nghiệp vụ (xuất kho tự động).
- Theo dõi thu tiền và công nợ khách hàng.

---

## 2) Quy trình chuẩn tổng quát (áp dụng mỗi ngày)

1. **Đầu ngày**: kiểm tra tồn kho và giá vốn (`Kho > Tồn kho hiện tại`).
2. **Tạo đơn bán** (`Bán hàng > Tạo đơn bán`) theo loại bán phù hợp.
3. **Lưu nháp đơn** để kiểm tra giá, số lượng, chiết khấu, VAT.
4. **Xác nhận đơn** tại màn hình chi tiết đơn.
5. Hệ thống tự động **tạo phiếu xuất kho** và **trừ tồn**.
6. Nếu còn nợ, vào **Phiếu thu tiền** để thu từng lần.
7. Cuối ngày đối chiếu:
	- `Bán hàng > Công nợ khách hàng`
	- `Kho > Đối chiếu số liệu`
	- `Bán hàng > Báo cáo doanh thu`

---

## 3) Quy trình bán lẻ

### Khi nào dùng
- Khách mua tại quầy, cần chốt nhanh.
- Mặc định thu tiền ngay.

### Các bước thao tác
1. Vào `Bán hàng > Tạo đơn bán`.
2. Chọn `Loại bán = Bán lẻ`.
3. Chọn kho xuất và thêm dòng hàng hóa.
4. Chọn phương thức thanh toán `Tiền mặt` hoặc `Chuyển khoản`.
5. Bấm **Lưu nháp**.
6. Mở chi tiết đơn và bấm **Xác nhận đơn & Trừ tồn kho**.

### Kết quả hệ thống
- Tạo phiếu xuất kho tự động.
- Trừ tồn kho ngay.
- Tự động ghi nhận đã thu đủ tiền (`Đã thu = Tổng thanh toán`, `Còn nợ = 0`) khi thanh toán tiền mặt/chuyển khoản.

---

## 4) Quy trình bán sỉ / bán gara

### Khi nào dùng
- Bán theo khách doanh nghiệp/gara/xưởng.
- Có thể cho nợ và thu sau.

### Các bước thao tác
1. Vào `Bán hàng > Tạo đơn bán`.
2. Chọn `Loại bán = Bán buôn` hoặc `Bán gara/xưởng`.
3. Chọn khách hàng (hoặc nhập thông tin khách nếu chưa có mã).
4. Chọn hàng, số lượng, giá bán, VAT.
5. Chọn phương thức thanh toán:
	- `Ghi nợ` nếu chưa thu ngay.
	- `Tiền mặt/Chuyển khoản` nếu khách trả ngay.
6. Bấm **Lưu nháp**.
7. Vào chi tiết đơn và bấm **Xác nhận đơn & Trừ tồn kho**.
8. Nếu còn nợ, vào `Bán hàng > Phiếu thu tiền` để thu dần.

### Kết quả hệ thống
- Tạo phiếu xuất kho và trừ tồn ngay khi xác nhận.
- Theo dõi công nợ theo từng đơn, từng khách.
- Phiếu thu sẽ tự cập nhật `Đã thu` và `Còn nợ`.

---

## 5) Quy tắc nghiệp vụ đã áp dụng trong code

1. Không cho xác nhận nếu đơn không còn ở trạng thái nháp.
2. Không cho xác nhận đơn không có dòng hàng.
3. Không cho số lượng bán nhỏ hơn hoặc bằng 0.
4. Không cho bán vượt tồn kho.
5. **Bán lẻ không được chọn ghi nợ**.
6. Bán sỉ/gara bắt buộc có thông tin khách hàng.
7. Khi xác nhận đơn:
	- Ghi phiếu xuất kho.
	- Trừ tồn kho.
	- Ghi nhận giá vốn và lợi nhuận từng dòng.
8. Phiếu thu không được vượt công nợ còn lại.

---

## 6) Hướng dẫn sử dụng nhanh cho nhân viên

### A. Nhập hàng đầu vào
1. `Kho > Tạo phiếu nhập`.
2. Nhập số lượng thực nhận và đơn giá.
3. Xác nhận phiếu nhập để tăng tồn và cập nhật giá vốn bình quân.

### B. Bán hàng trong ngày
1. Tạo đơn bán theo loại (lẻ/sỉ/gara).
2. Kiểm tra tồn kho theo cột tồn trong form.
3. Lưu nháp rồi xác nhận đơn.

### C. Thu nợ khách sỉ
1. `Bán hàng > Phiếu thu tiền`.
2. Chọn đơn còn nợ.
3. Nhập số tiền thu, lưu phiếu.
4. Kiểm tra lại công nợ giảm đúng.

### D. Đối chiếu cuối ngày
1. `Kho > Đối chiếu số liệu` để xem giá vốn xuất và tồn hiện tại.
2. `Bán hàng > Báo cáo doanh thu` để xem doanh thu/lợi nhuận.
3. `Bán hàng > Công nợ khách hàng` để xem danh sách còn nợ.

---

## 7) Gợi ý phân quyền vận hành

- **Nhân viên bán hàng**: tạo đơn, xác nhận đơn, lập phiếu thu.
- **Kế toán bán hàng**: theo dõi công nợ, rà soát phiếu thu, báo cáo doanh thu.
- **Quản lý kho/kế toán kho**: kiểm soát nhập, tồn, đối chiếu giá vốn.

---

## 8) Checklist kiểm tra lỗi thường gặp

1. Không xác nhận được đơn -> kiểm tra tồn kho đủ chưa.
2. Bán lẻ nhưng chọn ghi nợ -> đổi sang tiền mặt/chuyển khoản.
3. Thu tiền không lưu được -> kiểm tra số thu có vượt công nợ không.
4. Báo cáo lệch -> chạy đối chiếu số liệu kho theo khoảng ngày.

---

## 9) Ví dụ thực tế: bán 1 món hàng từ đầu đến cuối

### Ví dụ A - Bán lẻ 1 món

Mục tiêu: bán 1 cái bugi cho khách lẻ, thu tiền ngay và xuất kho luôn.

1. Vào `Bán hàng > Tạo đơn bán`.
2. Chọn:
	- Loại bán: `Bán lẻ`
	- Kho xuất: `Kho Cửa Hàng Chính`
	- Phương thức thanh toán: `Tiền mặt`
3. Ở chi tiết hàng hóa:
	- Chọn hàng `BUG-TT-01 - Bugi Iridium Toyota`
	- Số lượng `1`
	- Đơn giá tự điền theo giá bán lẻ.
4. Bấm **Lưu nháp**.
5. Vào chi tiết đơn, bấm **Xác nhận đơn & Trừ tồn kho**.
6. Kiểm tra kết quả:
	- Đơn trạng thái `Đã xác nhận`
	- `Đã thu = Tổng thanh toán`
	- `Còn nợ = 0`
	- Màn hình `Kho > Tồn kho` giảm 1 đơn vị.

### Ví dụ B - Bán sỉ 1 món

Mục tiêu: bán 1 bộ má phanh cho gara, cho nợ và thu sau 1 phần.

1. Vào `Bán hàng > Tạo đơn bán`.
2. Chọn:
	- Loại bán: `Bán buôn`
	- Khách hàng: `Gara Thành Đạt`
	- Phương thức thanh toán: `Ghi nợ`
3. Ở chi tiết hàng hóa:
	- Chọn `MA-PHANH-TRUOC`
	- Số lượng `1`
	- Đơn giá theo giá bán buôn.
4. Bấm **Lưu nháp** và **Xác nhận đơn & Trừ tồn kho**.
5. Thu tiền đợt 1:
	- Vào `Bán hàng > Phiếu thu tiền`
	- Chọn đơn vừa tạo
	- Nhập số tiền muốn thu (nhỏ hơn hoặc bằng công nợ)
	- Lưu phiếu thu.
6. Kiểm tra kết quả:
	- Tồn kho đã giảm
	- Công nợ giảm theo số tiền vừa thu
	- Đơn vẫn theo dõi phần nợ còn lại.

---

## 10) Khởi tạo CSDL demo theo đúng quy trình

Bạn có thể dựng toàn bộ dữ liệu demo bằng 1 lệnh:

1. Mở terminal tại thư mục dự án.
2. Chạy `init_full_demo.bat`.

Script sẽ tự:
- migrate CSDL,
- tạo danh mục,
- nhập kho ban đầu,
- tạo 1 đơn bán lẻ đã xuất kho,
- tạo 1 đơn bán sỉ có công nợ + phiếu thu đợt 1.
