# import os
# import django
# import datetime
# import sys
# import io
# from decimal import Decimal

# # Cấu hình UTF-8 cho terminal để in tiếng Việt không bị lỗi trên Windows
# if sys.stdout.encoding != 'utf-8':
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# # Thiết lập môi trường Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
# django.setup()

# from django.contrib.auth.models import User
# from apps.danh_muc.models import Kho, TaiKhoanKeToan, ViTriKho, DonViTinh, NhomHang, HangHoa, KhachHang
# from apps.kho.models import PhieuXuat, PhieuXuat_CT

# def init_danh_muc_co_ban():
#     print("=== [Step 1] Khởi tạo Danh mục cơ bản ===")
    
#     # 1. Kho hàng
#     kho_chinh, created = Kho.objects.get_or_create(
#         ma_kho='KHO_CHINH', 
#         defaults={'ten_kho': 'Kho chính Hà Nội', 'dia_chi': '123 Cầu Giấy, Hà Nội'}
#     )
#     if created: print("✓ Tạo Kho chính thành công")
    
#     # 2. Đơn vị tính
#     dvts = ['Cái', 'Bộ', 'Thùng']
#     for ten in dvts:
#         DonViTinh.objects.get_or_create(ten=ten)
#     print(f"✓ Đã khởi tạo {len(dvts)} Đơn vị tính")

#     # 3. Nhóm hàng
#     nhoms = [
#         ('PT', 'Phụ tùng máy', 15),
#         ('LOP', 'Lốp xe & Mâm', 10),
#         ('PK', 'Phụ kiện trang trí', 20),
#     ]
#     for ma, ten, bien_do in nhoms:
#         NhomHang.objects.get_or_create(ma_nhom=ma, defaults={'ten_nhom': ten, 'bien_do_loi_nhuan': bien_do})
#     print(f"✓ Đã khởi tạo {len(nhoms)} Nhóm hàng")

#     # 4. Tài khoản kế toán (KHÔI PHỤC ĐẦY ĐỦ 9 TÀI KHOẢN)
#     accounts = [
#         ('1111', 'Tiền mặt'),
#         ('1121', 'Tiền gửi ngân hàng (VND)'),
#         ('131', 'Phải thu khách hàng'),
#         ('156', 'Hàng hóa'),
#         ('331', 'Phải trả người bán'),
#         ('511', 'Doanh thu bán hàng'),
#         ('632', 'Giá vốn hàng bán'),
#         ('642', 'Chi phí quản lý doanh nghiệp'),
#         ('911', 'Xác nhận kết quả kinh doanh'),
#     ]
#     count_new_tk = 0
#     for ma, ten in accounts:
#         _, created = TaiKhoanKeToan.objects.get_or_create(ma_tk=ma, defaults={'ten_tk': ten})
#         if created: count_new_tk += 1
#     print(f"✓ Đã đồng bộ hệ thống {len(accounts)} Tài khoản kế toán (Thêm mới: {count_new_tk})")

# def init_vi_tri_kho():
#     print("\n=== [Step 2] Khởi tạo Vị trí kho (ĐẦY ĐỦ 62 VỊ TRÍ) ===")
#     kho_chinh = Kho.objects.filter(ma_kho='KHO_CHINH').first()
#     if not kho_chinh:
#         print("❌ Lỗi: Không tìm thấy Kho chính để gán vị trí")
#         return

#     vitri_data = [
#         {"ma": "A1-01", "mota": "Kệ A1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K01-T01", "mota": "Ben A - Day 1 - Ke 1 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K01-T02", "mota": "Ben A - Day 1 - Ke 1 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K01-T03", "mota": "Ben A - Day 1 - Ke 1 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K02-T01", "mota": "Ben A - Day 1 - Ke 2 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K02-T02", "mota": "Ben A - Day 1 - Ke 2 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K02-T03", "mota": "Ben A - Day 1 - Ke 2 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K03-T01", "mota": "Ben A - Day 1 - Ke 3 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K03-T02", "mota": "Ben A - Day 1 - Ke 3 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K03-T03", "mota": "Ben A - Day 1 - Ke 3 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K04-T01", "mota": "Ben A - Day 1 - Ke 4 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K04-T02", "mota": "Ben A - Day 1 - Ke 4 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K04-T03", "mota": "Ben A - Day 1 - Ke 4 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K01-T02", "mota": "", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K01-T04", "mota": "Bên A - Dãy 1 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K01-T05", "mota": "Bên A - Dãy 1 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K02-T04", "mota": "Bên A - Dãy 1 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K02-T05", "mota": "Bên A - Dãy 1 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K03-T04", "mota": "Bên A - Dãy 1 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K03-T05", "mota": "Bên A - Dãy 1 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K04-T04", "mota": "Bên A - Dãy 1 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D01-K04-T05", "mota": "Bên A - Dãy 1 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K01-T01", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K01-T03", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K01-T04", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K01-T05", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K02-T01", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K02-T02", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K02-T03", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K02-T04", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K02-T05", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K03-T01", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K03-T02", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K03-T03", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K03-T04", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K03-T05", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K04-T01", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K04-T02", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K04-T03", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K04-T04", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D02-K04-T05", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K01-T01", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K01-T02", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K01-T03", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K01-T04", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K01-T05", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K02-T01", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K02-T02", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K02-T03", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K02-T04", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K02-T05", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K03-T01", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K03-T02", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K03-T03", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K03-T04", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K03-T05", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K04-T01", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K04-T02", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K04-T03", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K04-T04", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "A-D03-K04-T05", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
#         {"ma": "HL-KHO_CHINH-01", "mota": "Vị trí hàng lỗi", "kho": "KHO_CHINH", "loai": "nho"},
#     ]

#     count_vt = 0
#     for v in vitri_data:
#         if not ViTriKho.objects.filter(ma_vi_tri=v['ma'], kho=kho_chinh).exists():
#             ViTriKho.objects.create(
#                 ma_vi_tri=v['ma'],
#                 mo_ta=v['mota'],
#                 kho=kho_chinh,
#                 loai_o=v['loai']
#             )
#             count_vt += 1
    
#     print(f"✓ Đã đồng bộ {count_vt} vị trí kho mới (Tổng: {len(vitri_data)})")

# def init_hang_hoa():
#     print("\n=== [Step 3] Khởi tạo Hàng hóa mẫu ===")
#     dvt_cai, _ = DonViTinh.objects.get_or_create(ten='Cái')
#     dvt_bo, _ = DonViTinh.objects.get_or_create(ten='Bộ')
#     nhom_pt, _ = NhomHang.objects.get_or_create(ma_nhom='PT', defaults={'ten_nhom': 'Phụ tùng máy'})
#     nhom_lop, _ = NhomHang.objects.get_or_create(ma_nhom='LOP', defaults={'ten_nhom': 'Lốp xe & Mâm'})

#     hang_data = [
#         ('HH001', 'Ắc quy GS Platinum 60Ah', dvt_cai, nhom_pt),
#         ('HH002', 'Lốp Michelin Primacy 4 215/50R17', dvt_cai, nhom_lop),
#         ('HH003', 'Bộ má phanh Brembo Premium', dvt_bo, nhom_pt),
#     ]
#     for ma, ten, dvt, nhom in hang_data:
#         HangHoa.objects.get_or_create(
#             ma_hang=ma, 
#             defaults={'ten_hang': ten, 'don_vi_tinh': dvt, 'nhom_hang': nhom, 'trang_thai': 'dang_ban'}
#         )
#     print(f"✓ Đã có 3 mặt hàng DEMO")

# def init_khach_hang():
#     print("\n=== [Step 4] Khởi tạo Khách hàng mẫu ===")
#     khs = [
#         ('KH001', 'Anh Tuấn - Gara Thành Công', '0912345678'),
#         ('KH002', 'Chị Linh - Cá nhân', '0988776655'),
#         ('KH003', 'Cửa hàng Phụ tùng 24h', '0243123456'),
#     ]
#     for ma, ten, sdt in khs:
#         KhachHang.objects.get_or_create(ma_kh=ma, defaults={'ten_kh': ten, 'so_dien_thoai': sdt, 'la_khach_hang': True})
#     print(f"✓ Đã thêm 3 Khách hàng mẫu")

# def init_phieu_xuat():
#     print("\n=== [Step 5] Khởi tạo Phiếu xuất kho mẫu ===")
#     admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
#     kho_chinh = Kho.objects.get(ma_kho='KHO_CHINH')
    
#     px_data = [
#         ('PX_DEMO_001', 'HH001', 2, 1500000),
#         ('PX_DEMO_002', 'HH002', 4, 2800000),
#         ('PX_DEMO_003', 'HH003', 1, 1200000),
#     ]

#     for so_phieu, ma_hang, sl, gia in px_data:
#         if not PhieuXuat.objects.filter(so_phieu=so_phieu).exists():
#             px = PhieuXuat.objects.create(
#                 so_phieu=so_phieu,
#                 kho=kho_chinh,
#                 ngay_lap=datetime.date.today(),
#                 ngay_hach_toan=datetime.date.today(),
#                 loai_xuat='ban_hang',
#                 trang_thai='1',
#                 nguoi_tao=admin_user,
#                 ghi_chu='Dữ liệu mẫu nạp tự động'
#             )
#             hang = HangHoa.objects.get(ma_hang=ma_hang)
#             PhieuXuat_CT.objects.create(
#                 phieu_xuat=px,
#                 hang_hoa=hang,
#                 so_luong=sl,
#                 gia_von=gia,
#                 tong_gia_von=sl * gia,
#                 tk_no='632',
#                 tk_co='156'
#             )
#             print(f"✓ Tạo phiếu xuất {so_phieu} thành công")
#     print("✓ Hoàn tất khởi tạo 3 Phiếu xuất DEMO")

# if __name__ == "__main__":
#     try:
#         init_danh_muc_co_ban()
#         init_vi_tri_kho()
#         init_hang_hoa()
#         init_khach_hang()
#         init_phieu_xuat()
#         print("\n" + "="*40)
#         print("KHỞI TẠO DỮ LIỆU Đầy ĐỦ 100% THÀNH CÔNG!")
#         print("="*40)
#     except Exception as e:
#         print(f"\n❌ LỖI KHỞI TẠO: {e}")
