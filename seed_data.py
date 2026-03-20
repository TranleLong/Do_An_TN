import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from django.contrib.auth.models import User
from apps.core.models import NhomHang, ThuongHieu, DonViTinh, HangHoa, Kho, ViTriKho
from apps.danh_muc.models import KhachHang, NhaCungCap

print("Starting seed data...")

# 1. User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
if not User.objects.filter(username='nhan_vien').exists():
    User.objects.create_user('nhan_vien', 'nv@example.com', 'nv123')

# 2. Danh mục Core
dvt1, _ = DonViTinh.objects.get_or_create(ten='Cái')
dvt2, _ = DonViTinh.objects.get_or_create(ten='Bộ')
dvt3, _ = DonViTinh.objects.get_or_create(ten='Hộp')

nh1, _ = NhomHang.objects.get_or_create(ma_nhom='DONG_CO', ten_nhom='Phụ tùng Động Cơ')
nh2, _ = NhomHang.objects.get_or_create(ma_nhom='GAM_MAY', ten_nhom='Phụ tùng Gầm Máy')
nh3, _ = NhomHang.objects.get_or_create(ma_nhom='DIEN_DC', ten_nhom='Phụ tùng Điện')

th1, _ = ThuongHieu.objects.get_or_create(ten='Toyota Genuine Parts')
th2, _ = ThuongHieu.objects.get_or_create(ten='Bosch')
th3, _ = ThuongHieu.objects.get_or_create(ten='Denso')

kho1, _ = Kho.objects.get_or_create(ma_kho='KHO_CHINH', ten_kho='Kho Cửa Hàng Chính')
kho2, _ = Kho.objects.get_or_create(ma_kho='KHO_PHU', ten_kho='Kho Phụ Tân Mai')

ViTriKho.objects.get_or_create(kho=kho1, ma_vi_tri='A1-01', mo_ta='Kệ A1, Tầng 1')
ViTriKho.objects.get_or_create(kho=kho1, ma_vi_tri='A1-02', mo_ta='Kệ A1, Tầng 2')

# 3. Hàng Hóa
hh1, _ = HangHoa.objects.get_or_create(ma_hang='BUG-TT-01', defaults={
    'ten_hang': 'Bugi Iridium Toyota', 'nhom_hang': nh3, 'thuong_hieu': th3,
    'don_vi_tinh': dvt1, 'gia_ban_le': 250000, 'gia_ban_buon': 220000,
    'xe_tuong_thich': 'Toyota Vios 2018-2022'
})
hh2, _ = HangHoa.objects.get_or_create(ma_hang='LOC-NHOT-01', defaults={
    'ten_hang': 'Lọc nhớt động cơ', 'nhom_hang': nh1, 'thuong_hieu': th1,
    'don_vi_tinh': dvt1, 'gia_ban_le': 150000, 'gia_ban_buon': 120000,
    'xe_tuong_thich': 'Toyota Innova, Fortuner'
})
hh3, _ = HangHoa.objects.get_or_create(ma_hang='MA-PHANH-TRUOC', defaults={
    'ten_hang': 'Má phanh trước (Bố thắng)', 'nhom_hang': nh2, 'thuong_hieu': th2,
    'don_vi_tinh': dvt2, 'gia_ban_le': 850000, 'gia_ban_buon': 780000,
    'xe_tuong_thich': 'Honda City, Civic'
})

# 4. Đối tác
KhachHang.objects.get_or_create(ma_kh='KH001', defaults={
    'ten_kh': 'Anh Tuấn Xửng', 'loai_kh': 'ca_nhan', 'so_dien_thoai': '0901234567'
})
KhachHang.objects.get_or_create(ma_kh='GR001', defaults={
    'ten_kh': 'Gara Ô tô Thành Đạt', 'loai_kh': 'gara', 'so_dien_thoai': '0988777666',
    'chiet_khau_mac_dinh': 5.0, 'han_muc_cong_no': 50000000
})

NhaCungCap.objects.get_or_create(ma_ncc='NCC001', defaults={
    'ten_ncc': 'Đại lý Phụ tùng Bosch VN', 'loai_ncc': 'dai_ly', 'so_dien_thoai': '19008888'
})
NhaCungCap.objects.get_or_create(ma_ncc='NCC002', defaults={
    'ten_ncc': 'Công ty CP Phụ Tùng Tín Phát', 'loai_ncc': 'nhap_khau', 'so_dien_thoai': '0243123456'
})

print("Seed data completed!")
