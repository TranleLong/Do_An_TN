# Ghi chu thiet ke kho theo muc chiem cho

## 1) Danh gia
Thiet ke muc_chiem_cho (1..50) la hop ly cho kho phu tung, de code va de van hanh hon cach mo phong kich thuoc that 100%.

## 2) Quy uoc nghiep vu
- Truong hang hoa: muc_chiem_cho (1..50).
- Suc chua tieu chuan moi o: 50 don vi.
- Dung luong su dung cua 1 dong ton vi tri: so_luong * muc_chiem_cho.

## 3) Cong thuc
- Tong dung luong can = so_luong_nhap * muc_chiem_cho.
- So o can = ceil(tong_dung_luong_can / 50).

## 4) Vi du
- muc_chiem_cho=1, nhap 35 -> ceil(35/50)=1 o.
- muc_chiem_cho=5, nhap 13 -> ceil(65/50)=2 o.
- muc_chiem_cho=25, nhap 5 -> ceil(125/50)=3 o.

## 5) CSDL can co
- core_hanghoa.muc_chiem_cho (1..50).
- core_vitrikho.suc_chua_toi_da (mac dinh 50).
- kho_tonkho_vitri de theo doi ton theo tung vi tri.

## 6) Trang thai o kho
- dung_luong_da_dung = SUM(so_luong * muc_chiem_cho).
- dung_luong_con_lai = suc_chua_toi_da - dung_luong_da_dung.
- DA_DAY khi con_lai <= 0.
- GAN_DAY khi 0 < con_lai <= 10.
- CON_TRONG khi con_lai > 10.

## 7) Hien thi khi bam vao 1 vi tri
Nen hien thi:
- Ma vi tri, ten kho.
- suc_chua_toi_da, dung_luong_da_dung, dung_luong_con_lai, trang_thai.
- Danh sach hang trong o: ma_hang, ten_hang, so_luong, muc_chiem_cho, dung_luong_su_dung.

## 8) Da trien khai trong code
- Them API chi tiet vi tri de click tren so do kho xem thong tin.
- Map kho cho phep bam vao o vi tri de mo popup chi tiet.
- Engine goi y nhap kho da tinh theo muc_chiem_cho va suc chua o.

## 9) Viec nen lam tiep
1. Them truong muc_chiem_cho vao man hinh danh muc hang hoa (UI nhap/sua).
2. Them bo loc mau tren so do (xanh/vang/do) theo trang thai o.
3. Them test cho case bien: muc_chiem_cho=1,50 va nhap so luong chia du.
4. Neu can truy vet lich su, bo sung snapshot muc_chiem_cho_tai_thoi_diem vao chi tiet nhap.

## 10) Cap nhat moi nhat theo yeu cau nghiep vu
- Danh muc hang hoa da bo 2 cot gia ban le/gia ban buon.
- Gia duoc nhap truc tiep tai cac phieu nghiep vu (nhap/xuat/ban) thay vi co dinh trong danh muc.
- Workflow trang thai cho phieu Ban/Nhap/Xuat da chuan hoa thanh 3 muc:
	- 1: Lap phieu
	- 2: Kho xu ly (Nhap kho hoac Xuat kho)
	- 3: So cai
- Da co migration chuyen du lieu trang thai cu sang ma moi de khong mat lich su.
- Da cap nhat man hinh danh sach/chi tiet de hien thi ma trang thai moi.
