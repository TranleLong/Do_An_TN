from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User

from apps.kho.models import (PhieuDieuChinhKiemKe, PhieuNhap, PhieuNhap_CT,
                             PhieuXuat, PhieuXuat_CT, TonKho)
from apps.kho.views import _gen_so_phieu

user = User.objects.filter(is_superuser=True).first() or User.objects.first()
created_in = 0
created_out = 0

for phieu in PhieuDieuChinhKiemKe.objects.filter(trang_thai='2'):
    tag = f'[KK_DC:{phieu.pk}]'
    if PhieuNhap.objects.filter(ghi_chu__contains=tag).exists() or PhieuXuat.objects.filter(ghi_chu__contains=tag).exists():
        continue

    rows = list(phieu.chi_tiet.select_related('hang_hoa'))
    tang_rows = [r for r in rows if int(r.chenh_lech or 0) > 0]
    giam_rows = [r for r in rows if int(r.chenh_lech or 0) < 0]

    gia_von_map = {}
    for r in rows:
        ton = TonKho.objects.filter(kho=phieu.kho, hang_hoa=r.hang_hoa).first()
        gia_von_map[r.hang_hoa_id] = Decimal(ton.gia_von_tb or 0) if ton else Decimal('0')

    if tang_rows:
        pn = PhieuNhap.objects.create(
            so_phieu=_gen_so_phieu('NK'),
            ngay_lap=date.today(),
            ngay_hach_toan=date.today(),
            ngay_chung_tu=date.today(),
            ngay_nhap=date.today(),
            loai_nhap='3',
            kho=phieu.kho,
            tong_tien=0,
            trang_thai='3',
            nguoi_tao=user,
            ghi_chu=f'Backfill điều chỉnh tăng từ phiếu {phieu.so_phieu} {tag}',
        )
        for r in tang_rows:
            PhieuNhap_CT.objects.create(
                phieu_nhap=pn,
                hang_hoa=r.hang_hoa,
                so_luong_dat=0,
                so_luong_nhan=int(r.chenh_lech or 0),
                don_gia=gia_von_map.get(r.hang_hoa_id, Decimal('0')),
                chiet_khau=0,
                thue_vat=0,
                tk_no='156',
                tk_co='711',
            )
        pn.tinh_tong()
        created_in += 1

    if giam_rows:
        px = PhieuXuat.objects.create(
            so_phieu=_gen_so_phieu('PX'),
            ngay_lap=date.today(),
            ngay_hach_toan=date.today(),
            ngay_chung_tu=date.today(),
            ngay_xuat=date.today(),
            loai_xuat='hu_hong',
            kho=phieu.kho,
            tong_gia_von=0,
            trang_thai='3',
            nguoi_tao=user,
            ghi_chu=f'Backfill điều chỉnh giảm từ phiếu {phieu.so_phieu} {tag}',
        )
        tong = Decimal('0')
        for r in giam_rows:
            sl_giam = abs(int(r.chenh_lech or 0))
            gia_von = gia_von_map.get(r.hang_hoa_id, Decimal('0'))
            tg_von = Decimal(sl_giam) * gia_von
            PhieuXuat_CT.objects.create(
                phieu_xuat=px,
                hang_hoa=r.hang_hoa,
                so_luong=sl_giam,
                gia_von=gia_von,
                tong_gia_von=tg_von,
                tk_no='632',
                tk_co='156',
            )
            tong += tg_von
        px.tong_gia_von = tong
        px.save(update_fields=['tong_gia_von'])
        created_out += 1

print(f'created_in={created_in}, created_out={created_out}')
