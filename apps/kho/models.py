"""
Models cho app Kho: TonKho, PhieuNhap, PhieuXuat, KiemKe
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import HangHoa, Kho, ViTriKho
from apps.danh_muc.models import NhaCungCap
import datetime


def generate_so_phieu(prefix):
    from django.utils import timezone
    now = timezone.now()
    return f"{prefix}-{now.strftime('%Y%m')}-{now.strftime('%H%M%S')}"


class TonKho(models.Model):
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.CASCADE, verbose_name='Hàng hóa')
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name='Kho')
    so_luong = models.IntegerField(default=0, verbose_name='Số lượng tồn')
    gia_von_tb = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Giá vốn TB')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hang_hoa', 'kho']
        verbose_name = 'Tồn kho'

    def __str__(self):
        return f"{self.hang_hoa.ma_hang} | {self.kho.ma_kho} | SL: {self.so_luong}"


class PhieuNhap(models.Model):
    LOAI_NHAP = [
        ('mua_ncc', 'Mua nhà cung cấp'),
        ('tra_hang_kh', 'Khách hàng trả hàng'),
        ('dieu_chinh', 'Điều chỉnh tồn kho'),
    ]
    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('da_nhap', 'Đã nhập kho'),
        ('huy', 'Đã hủy'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu nhập')
    ngay_nhap = models.DateField(default=datetime.date.today, verbose_name='Ngày nhập')
    loai_nhap = models.CharField(max_length=20, choices=LOAI_NHAP, default='mua_ncc',
                                  verbose_name='Loại nhập')
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name='Nhà cung cấp')
    so_hd_ncc = models.CharField(max_length=50, blank=True, verbose_name='Số HĐ NCC')
    ngay_hd_ncc = models.DateField(null=True, blank=True, verbose_name='Ngày HĐ NCC')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho nhập')
    tong_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Tổng tiền')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='nhap',
                                   verbose_name='Trạng thái')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   verbose_name='Người tạo')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu nhập kho'
        verbose_name_plural = 'Phiếu nhập kho'
        ordering = ['-ngay_nhap', '-ngay_tao']

    def __str__(self):
        return f"{self.so_phieu} ({self.get_trang_thai_display()})"

    def tinh_tong(self):
        tong = sum(ct.thanh_tien for ct in self.chi_tiet.all())
        self.tong_tien = tong
        self.save(update_fields=['tong_tien'])
        return tong

    def xac_nhan_nhap_kho(self):
        """Cập nhật tồn kho theo phương pháp bình quân gia quyền"""
        if self.trang_thai != 'nhap':
            return False
        for ct in self.chi_tiet.all():
            ton_kho, created = TonKho.objects.get_or_create(
                hang_hoa=ct.hang_hoa, kho=self.kho,
                defaults={'so_luong': 0, 'gia_von_tb': 0}
            )
            sl_cu = ton_kho.so_luong
            gv_cu = ton_kho.gia_von_tb
            sl_nhap = ct.so_luong_nhan
            gv_nhap = ct.don_gia

            if sl_cu + sl_nhap > 0:
                gv_moi = (sl_cu * gv_cu + sl_nhap * gv_nhap) / (sl_cu + sl_nhap)
            else:
                gv_moi = gv_nhap

            ton_kho.so_luong = sl_cu + sl_nhap
            ton_kho.gia_von_tb = round(gv_moi, 0)
            ton_kho.save()
        self.trang_thai = 'da_nhap'
        self.save(update_fields=['trang_thai'])
        return True


class PhieuNhap_CT(models.Model):
    phieu_nhap = models.ForeignKey(PhieuNhap, on_delete=models.CASCADE,
                                    related_name='chi_tiet', verbose_name='Phiếu nhập')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong_dat = models.IntegerField(default=0, verbose_name='SL đặt')
    so_luong_nhan = models.IntegerField(verbose_name='SL thực nhận')
    don_gia = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='Đơn giá')
    chiet_khau = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                      verbose_name='CK (%)')
    thue_vat = models.DecimalField(max_digits=5, decimal_places=2, default=10,
                                    verbose_name='VAT (%)')
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                      verbose_name='Thành tiền')
    so_lo = models.CharField(max_length=50, blank=True, verbose_name='Số lô')
    han_su_dung = models.DateField(null=True, blank=True, verbose_name='Hạn SD')

    class Meta:
        verbose_name = 'Chi tiết phiếu nhập'

    def save(self, *args, **kwargs):
        ck = self.don_gia * self.chiet_khau / 100
        vat = (self.don_gia - ck) * self.thue_vat / 100
        self.thanh_tien = round((self.don_gia - ck + vat) * self.so_luong_nhan, 0)
        super().save(*args, **kwargs)


class PhieuXuat(models.Model):
    LOAI_XUAT = [
        ('ban_hang', 'Xuất bán hàng'),
        ('tra_ncc', 'Trả nhà cung cấp'),
        ('noi_bo', 'Xuất nội bộ'),
        ('hu_hong', 'Hư hỏng / Hao hụt'),
    ]
    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('da_xuat', 'Đã xuất kho'),
        ('huy', 'Đã hủy'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu xuất')
    ngay_xuat = models.DateField(default=datetime.date.today, verbose_name='Ngày xuất')
    loai_xuat = models.CharField(max_length=20, choices=LOAI_XUAT, default='ban_hang',
                                  verbose_name='Loại xuất')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho xuất')
    tong_gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                        verbose_name='Tổng giá vốn')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='nhap',
                                   verbose_name='Trạng thái')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   verbose_name='Người tạo')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu xuất kho'
        ordering = ['-ngay_xuat', '-ngay_tao']

    def __str__(self):
        return f"{self.so_phieu}"


class PhieuXuat_CT(models.Model):
    phieu_xuat = models.ForeignKey(PhieuXuat, on_delete=models.CASCADE,
                                    related_name='chi_tiet', verbose_name='Phiếu xuất')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong = models.IntegerField(verbose_name='Số lượng')
    gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                   verbose_name='Giá vốn/đv')
    tong_gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                        verbose_name='Tổng giá vốn')

    class Meta:
        verbose_name = 'Chi tiết phiếu xuất'


class KiemKe(models.Model):
    TRANG_THAI = [
        ('dang_kiem', 'Đang kiểm kê'),
        ('da_duyet', 'Đã duyệt & điều chỉnh'),
    ]
    ngay_kiem_ke = models.DateField(default=datetime.date.today, verbose_name='Ngày kiểm kê')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho')
    nguoi_kiem = models.CharField(max_length=100, blank=True, verbose_name='Người kiểm kê')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='dang_kiem')
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu kiểm kê'
        ordering = ['-ngay_kiem_ke']

    def __str__(self):
        return f"Kiểm kê {self.kho.ten_kho} - {self.ngay_kiem_ke}"


class KiemKe_CT(models.Model):
    kiem_ke = models.ForeignKey(KiemKe, on_delete=models.CASCADE, related_name='chi_tiet')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong_so_sach = models.IntegerField(verbose_name='SL sổ sách')
    so_luong_thuc_te = models.IntegerField(verbose_name='SL thực tế')
    chenh_lech = models.IntegerField(default=0, verbose_name='Chênh lệch')
    ly_do = models.CharField(max_length=200, blank=True, verbose_name='Lý do chênh lệch')

    def save(self, *args, **kwargs):
        self.chenh_lech = self.so_luong_thuc_te - self.so_luong_so_sach
        super().save(*args, **kwargs)
