from decimal import Decimal

from apps.kho.models import PhieuXuat, PhieuXuat_CT, TonKho
from django.db import transaction
from django.utils import timezone


class DonBanService:
    @staticmethod
    def _gen_so_phieu_xuat():
        base = timezone.now().strftime('%Y%m%d-%H%M%S-%f')
        so_phieu = f"XK-{base}"
        if not PhieuXuat.objects.filter(so_phieu=so_phieu).exists():
            return so_phieu

        suffix = 1
        while True:
            candidate = f"{so_phieu}-{suffix}"
            if not PhieuXuat.objects.filter(so_phieu=candidate).exists():
                return candidate
            suffix += 1

    @staticmethod
    def _validate_xac_nhan(don):
        if don.trang_thai != 'nhap':
            return False, "Đơn đã được xử lý", []

        chi_tiet = list(don.chi_tiet.select_related('hang_hoa'))
        if not chi_tiet:
            return False, "Đơn bán chưa có hàng hóa", []

        if don.loai_ban == 'ban_le' and don.phuong_thuc_tt == 'no':
            return False, "Bán lẻ không cho phép ghi nợ. Vui lòng chọn tiền mặt/chuyển khoản.", []

        if don.loai_ban in ('ban_buon', 'ban_gara') and not (don.khach_hang_id or don.ten_kh.strip()):
            return False, "Bán sỉ/gara cần có thông tin khách hàng", []

        for ct in chi_tiet:
            if ct.so_luong <= 0:
                return False, f"Số lượng phải lớn hơn 0: {ct.hang_hoa.ten_hang}", []

            ton = TonKho.objects.filter(hang_hoa=ct.hang_hoa, kho=don.kho).first()
            if not ton or ton.so_luong < ct.so_luong:
                return False, f"Không đủ tồn kho: {ct.hang_hoa.ten_hang}", []

        return True, "OK", chi_tiet

    @staticmethod
    @transaction.atomic
    def xac_nhan_don_ban(don):
        ok, msg, chi_tiet = DonBanService._validate_xac_nhan(don)
        if not ok:
            return False, msg

        phieu_xuat = PhieuXuat.objects.create(
            so_phieu=DonBanService._gen_so_phieu_xuat(),
            ngay_xuat=don.ngay_ban,
            loai_xuat='ban_hang',
            kho=don.kho,
            nguoi_tao=don.nhan_vien_ban,
            trang_thai='da_xuat',
            ghi_chu=f"Xuất từ đơn {don.so_don} - {don.get_loai_ban_display()}"
        )

        tong_gia_von = Decimal('0')
        for ct in chi_tiet:
            ton = TonKho.objects.select_for_update().get(hang_hoa=ct.hang_hoa, kho=don.kho)
            gia_von = ton.gia_von_tb
            tong_von_dong = gia_von * ct.so_luong

            ct.gia_von = gia_von
            ct.loi_nhuan = ct.thanh_tien - tong_von_dong
            ct.save(update_fields=['gia_von', 'loi_nhuan'])

            PhieuXuat_CT.objects.create(
                phieu_xuat=phieu_xuat,
                hang_hoa=ct.hang_hoa,
                so_luong=ct.so_luong,
                gia_von=gia_von,
                tong_gia_von=tong_von_dong,
            )

            ton.so_luong -= ct.so_luong
            ton.save(update_fields=['so_luong', 'ngay_cap_nhat'])

            tong_gia_von += tong_von_dong

        phieu_xuat.tong_gia_von = tong_gia_von
        phieu_xuat.save(update_fields=['tong_gia_von'])

        don.trang_thai = 'da_xac_nhan'
        if don.phuong_thuc_tt in ('tien_mat', 'chuyen_khoan'):
            don.da_thu = don.tong_thanh_toan
            don.con_no = 0
        else:
            don.con_no = don.tong_thanh_toan - don.da_thu

        don.save(update_fields=['trang_thai', 'da_thu', 'con_no'])

        if don.loai_ban == 'ban_le':
            return True, "Xác nhận thành công: đã xuất kho và hoàn tất thu tiền đơn bán lẻ"

        if don.phuong_thuc_tt == 'no':
            return True, "Xác nhận thành công: đã xuất kho, theo dõi công nợ cho đơn sỉ/gara"

        return True, "Xác nhận thành công: đã xuất kho và ghi nhận thanh toán"
