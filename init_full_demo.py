import os
from datetime import date
from decimal import Decimal

import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.ban_hang.models import DonBan, DonBan_CT, PhieuThu
from apps.core.models import (DonViTinh, HangHoa, Kho, NhomHang, ThuongHieu,
                              ViTriKho)
from apps.danh_muc.models import KhachHang, NhaCungCap
from apps.kho.models import (KiemKe, KiemKe_CT, PhieuNhap, PhieuNhap_CT,
                             PhieuXuat, PhieuXuat_CT, TonKho)
from django.contrib.auth.models import User


def create_users():
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if not admin.is_superuser:
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=['is_staff', 'is_superuser'])
    admin.set_password('admin123')
    admin.save(update_fields=['password'])

    nhan_vien, _ = User.objects.get_or_create(
        username='nhan_vien',
        defaults={'email': 'nv@example.com'},
    )
    nhan_vien.set_password('nv123')
    nhan_vien.save(update_fields=['password'])
    return admin, nhan_vien


def create_master_data():
    dvt_cai, _ = DonViTinh.objects.get_or_create(ten='Cái')
    dvt_bo, _ = DonViTinh.objects.get_or_create(ten='Bộ')

    nh_dong_co, _ = NhomHang.objects.get_or_create(ma_nhom='DONG_CO', defaults={'ten_nhom': 'Phụ tùng Động Cơ'})
    nh_gam_may, _ = NhomHang.objects.get_or_create(ma_nhom='GAM_MAY', defaults={'ten_nhom': 'Phụ tùng Gầm Máy'})

    th_denso, _ = ThuongHieu.objects.get_or_create(ten='Denso')
    th_bosch, _ = ThuongHieu.objects.get_or_create(ten='Bosch')

    kho_chinh, _ = Kho.objects.get_or_create(ma_kho='KHO_CHINH', defaults={'ten_kho': 'Kho Cửa Hàng Chính'})
    ViTriKho.objects.get_or_create(kho=kho_chinh, ma_vi_tri='A1-01', defaults={'mo_ta': 'Kệ A1'})

    hh_bugi, _ = HangHoa.objects.get_or_create(
        ma_hang='BUG-TT-01',
        defaults={
            'ten_hang': 'Bugi Iridium Toyota',
            'nhom_hang': nh_dong_co,
            'thuong_hieu': th_denso,
            'don_vi_tinh': dvt_cai,
            'gia_ban_le': Decimal('250000'),
            'gia_ban_buon': Decimal('220000'),
            'xe_tuong_thich': 'Toyota Vios 2018-2022',
        },
    )

    hh_ma_phanh, _ = HangHoa.objects.get_or_create(
        ma_hang='MA-PHANH-TRUOC',
        defaults={
            'ten_hang': 'Má phanh trước',
            'nhom_hang': nh_gam_may,
            'thuong_hieu': th_bosch,
            'don_vi_tinh': dvt_bo,
            'gia_ban_le': Decimal('850000'),
            'gia_ban_buon': Decimal('780000'),
            'xe_tuong_thich': 'Honda City, Civic',
        },
    )

    kh_le, _ = KhachHang.objects.get_or_create(
        ma_kh='KH001',
        defaults={
            'ten_kh': 'Khách lẻ mẫu',
            'loai_kh': 'ca_nhan',
            'so_dien_thoai': '0901234567',
        },
    )

    kh_gara, _ = KhachHang.objects.get_or_create(
        ma_kh='GR001',
        defaults={
            'ten_kh': 'Gara Thành Đạt',
            'loai_kh': 'gara',
            'so_dien_thoai': '0988777666',
            'chiet_khau_mac_dinh': Decimal('5'),
            'han_muc_cong_no': Decimal('50000000'),
        },
    )

    ncc, _ = NhaCungCap.objects.get_or_create(
        ma_ncc='NCC001',
        defaults={
            'ten_ncc': 'Đại lý Bosch VN',
            'loai_ncc': 'dai_ly',
            'so_dien_thoai': '19008888',
        },
    )

    return {
        'kho': kho_chinh,
        'hh_bugi': hh_bugi,
        'hh_ma_phanh': hh_ma_phanh,
        'kh_le': kh_le,
        'kh_gara': kh_gara,
        'ncc': ncc,
    }


def reset_transaction_data():
    PhieuThu.objects.all().delete()
    DonBan_CT.objects.all().delete()
    DonBan.objects.all().delete()
    PhieuXuat_CT.objects.all().delete()
    PhieuXuat.objects.all().delete()
    PhieuNhap_CT.objects.all().delete()
    PhieuNhap.objects.all().delete()
    KiemKe_CT.objects.all().delete()
    KiemKe.objects.all().delete()
    TonKho.objects.all().delete()


def create_opening_stock(data, user):
    phieu_nhap = PhieuNhap.objects.create(
        so_phieu='PN-DEMO-001',
        ngay_nhap=date.today(),
        loai_nhap='mua_ncc',
        nha_cung_cap=data['ncc'],
        kho=data['kho'],
        nguoi_tao=user,
        ghi_chu='Nhập kho ban đầu cho dữ liệu demo',
    )

    PhieuNhap_CT.objects.create(
        phieu_nhap=phieu_nhap,
        hang_hoa=data['hh_bugi'],
        so_luong_dat=50,
        so_luong_nhan=50,
        don_gia=Decimal('180000'),
        chiet_khau=Decimal('0'),
        thue_vat=Decimal('10'),
    )

    PhieuNhap_CT.objects.create(
        phieu_nhap=phieu_nhap,
        hang_hoa=data['hh_ma_phanh'],
        so_luong_dat=20,
        so_luong_nhan=20,
        don_gia=Decimal('600000'),
        chiet_khau=Decimal('0'),
        thue_vat=Decimal('10'),
    )

    phieu_nhap.tinh_tong()
    phieu_nhap.xac_nhan_nhap_kho()


def create_retail_sale(data, user):
    don = DonBan.objects.create(
        so_don='BH-LE-DEMO-001',
        ngay_ban=date.today(),
        loai_ban='ban_le',
        khach_hang=data['kh_le'],
        ten_kh=data['kh_le'].ten_kh,
        sdt_kh=data['kh_le'].so_dien_thoai,
        kho=data['kho'],
        nhan_vien_ban=user,
        phuong_thuc_tt='tien_mat',
        chiet_khau_dh=Decimal('0'),
        ghi_chu='Đơn demo bán lẻ 1 món hàng',
    )

    DonBan_CT.objects.create(
        don_ban=don,
        hang_hoa=data['hh_bugi'],
        so_luong=1,
        don_gia=data['hh_bugi'].gia_ban_le,
        chiet_khau=Decimal('0'),
        thue_vat=Decimal('10'),
    )

    don.tinh_tong()
    ok, msg = don.xac_nhan_don_ban()
    if not ok:
        raise RuntimeError(f'Không thể xác nhận đơn bán lẻ: {msg}')
    return don


def create_wholesale_sale(data, user):
    don = DonBan.objects.create(
        so_don='BH-SI-DEMO-001',
        ngay_ban=date.today(),
        loai_ban='ban_buon',
        khach_hang=data['kh_gara'],
        ten_kh=data['kh_gara'].ten_kh,
        sdt_kh=data['kh_gara'].so_dien_thoai,
        kho=data['kho'],
        nhan_vien_ban=user,
        phuong_thuc_tt='no',
        chiet_khau_dh=Decimal('0'),
        ghi_chu='Đơn demo bán sỉ có công nợ',
    )

    DonBan_CT.objects.create(
        don_ban=don,
        hang_hoa=data['hh_ma_phanh'],
        so_luong=3,
        don_gia=data['hh_ma_phanh'].gia_ban_buon,
        chiet_khau=Decimal('3'),
        thue_vat=Decimal('10'),
    )

    don.tinh_tong()
    ok, msg = don.xac_nhan_don_ban()
    if not ok:
        raise RuntimeError(f'Không thể xác nhận đơn bán sỉ: {msg}')

    thu_dot_1 = Decimal('1000000') if don.con_no > Decimal('1000000') else don.con_no
    if thu_dot_1 > 0:
        PhieuThu.objects.create(
            so_phieu='PT-DEMO-001',
            ngay_thu=date.today(),
            khach_hang=data['kh_gara'],
            hinh_thuc_thu='chuyen_khoan',
            tong_thu=thu_dot_1,
            don_ban=don,
            ghi_chu='Thu đợt 1 cho đơn bán sỉ demo',
            nguoi_tao=user,
        )
        don.da_thu += thu_dot_1
        don.con_no = don.tong_thanh_toan - don.da_thu
        don.save(update_fields=['da_thu', 'con_no'])

    return don


@transaction.atomic
def run():
    print('=== INIT FULL DEMO ERP ===')
    admin, nhan_vien = create_users()
    data = create_master_data()
    reset_transaction_data()
    create_opening_stock(data, admin)
    don_le = create_retail_sale(data, nhan_vien)
    don_si = create_wholesale_sale(data, nhan_vien)

    ton_bugi = TonKho.objects.get(hang_hoa=data['hh_bugi'], kho=data['kho']).so_luong
    ton_ma_phanh = TonKho.objects.get(hang_hoa=data['hh_ma_phanh'], kho=data['kho']).so_luong

    print('Khởi tạo thành công!')
    print(f'- Đơn bán lẻ đã xác nhận: {don_le.so_don}')
    print(f'- Đơn bán sỉ đã xác nhận: {don_si.so_don}')
    print(f'- Công nợ còn lại đơn sỉ: {don_si.con_no:,.0f} đ')
    print(f'- Tồn BUG-TT-01 còn: {ton_bugi}')
    print(f'- Tồn MA-PHANH-TRUOC còn: {ton_ma_phanh}')
    print('Tài khoản đăng nhập: admin/admin123 hoặc nhan_vien/nv123')


if __name__ == '__main__':
    run()
    run()
