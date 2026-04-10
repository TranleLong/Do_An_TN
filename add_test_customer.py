#!/usr/bin/env python
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.danh_muc.models import KhachHang

# Thêm 1 khách hàng kinh doanh với MST để test
kh_test = KhachHang.objects.create(
    ma_kh='KH999',
    ten_kh='Công ty TNHH ABC',
    loai_kh='doanh_nghiep',
    ma_so_thue='0123456789',
    dia_chi='123 Đường Láng, Hà Nội',
    so_dien_thoai='0987654321',
    email='abc@company.com.vn',
    han_muc_cong_no=50000000,
    so_ngay_no_max=30,
    chiet_khau_mac_dinh=5.0
)

print(f"✓ Đã thêm khách hàng test:")
print(f"  Mã KH: {kh_test.ma_kh}")
print(f"  Tên: {kh_test.ten_kh}")
print(f"  MST: {kh_test.ma_so_thue}")
print(f"\nDùng MST này để test AJAX lookup: 0123456789")
print(f"\nDùng MST này để test AJAX lookup: 0123456789")
