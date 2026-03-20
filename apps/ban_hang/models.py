"""
Models cho app Ban Hàng: DonBan, PhieuThu, PhieuTraHang
"""
import datetime

from apps.core.models import HangHoa, Kho
from apps.danh_muc.models import KhachHang
from django.contrib.auth.models import User
from django.db import models


class DonBan(models.Model):
    LOAI_BAN = [
        ('ban_le', 'Bán lẻ'),
        ('ban_buon', 'Bán buôn'),
        ('ban_gara', 'Bán gara/xưởng'),
    ]
    PHUONG_THUC_TT = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('no', 'Ghi nợ'),
    ]
    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('huy', 'Đã hủy'),
    ]
    so_don = models.CharField(max_length=30, unique=True, verbose_name='Số đơn bán')
    ngay_ban = models.DateField(default=datetime.date.today, verbose_name='Ngày bán')
    loai_ban = models.CharField(max_length=20, choices=LOAI_BAN, default='ban_le',
                                 verbose_name='Loại bán')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Khách hàng')
    ten_kh = models.CharField(max_length=200, blank=True, verbose_name='Tên KH')
    sdt_kh = models.CharField(max_length=15, blank=True, verbose_name='SĐT KH')
    xe_kh = models.CharField(max_length=100, blank=True, verbose_name='Xe KH')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho xuất')
    nhan_vien_ban = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                       verbose_name='Nhân viên bán')
    phuong_thuc_tt = models.CharField(max_length=20, choices=PHUONG_THUC_TT,
                                       default='tien_mat', verbose_name='PTTT')
    tong_tien_hang = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    chiet_khau_dh = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                         verbose_name='Chiết khấu đơn hàng')
    tong_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tong_thanh_toan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                           verbose_name='Tổng thanh toán')
    da_thu = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                  verbose_name='Đã thu')
    con_no = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                  verbose_name='Còn nợ')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='nhap',
                                   verbose_name='Trạng thái')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Đơn bán hàng'
        verbose_name_plural = 'Đơn bán hàng'
        ordering = ['-ngay_ban', '-ngay_tao']

    def __str__(self):
        return f"{self.so_don} - {self.ten_kh or 'Khách lẻ'}"

    def tinh_tong(self):
        tong_hang = sum(ct.thanh_tien for ct in self.chi_tiet.all())
        tong_thue = sum(ct.tien_thue for ct in self.chi_tiet.all())
        self.tong_tien_hang = tong_hang
        self.tong_thue = tong_thue
        self.tong_thanh_toan = tong_hang + tong_thue - self.chiet_khau_dh
        self.con_no = self.tong_thanh_toan - self.da_thu
        self.save(update_fields=['tong_tien_hang', 'tong_thue', 'tong_thanh_toan', 'con_no'])

    def xac_nhan_don_ban(self):
        """Xuất kho và xác nhận đơn bán"""
        from .services import DonBanService

        return DonBanService.xac_nhan_don_ban(self)


class DonBan_CT(models.Model):
    don_ban = models.ForeignKey(DonBan, on_delete=models.CASCADE,
                                 related_name='chi_tiet', verbose_name='Đơn bán')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong = models.IntegerField(verbose_name='Số lượng')
    don_gia = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='Đơn giá')
    chiet_khau = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                      verbose_name='CK (%)')
    thue_vat = models.DecimalField(max_digits=5, decimal_places=2, default=10,
                                    verbose_name='VAT (%)')
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                      verbose_name='Thành tiền')
    tien_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Tiền thuế')
    gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                   verbose_name='Giá vốn')
    loi_nhuan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Lợi nhuận')

    def save(self, *args, **kwargs):
        ck = self.don_gia * self.chiet_khau / 100
        gia_sau_ck = (self.don_gia - ck) * self.so_luong
        self.tien_thue = round(gia_sau_ck * self.thue_vat / 100, 0)
        self.thanh_tien = round(gia_sau_ck, 0)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Chi tiết đơn bán'


class PhieuThu(models.Model):
    HINH_THUC = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu thu')
    ngay_thu = models.DateField(default=datetime.date.today, verbose_name='Ngày thu')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.PROTECT, verbose_name='Khách hàng')
    hinh_thuc_thu = models.CharField(max_length=20, choices=HINH_THUC, default='tien_mat')
    so_tk_nh = models.CharField(max_length=100, blank=True, verbose_name='Số TK NH')
    so_tham_chieu = models.CharField(max_length=100, blank=True, verbose_name='Mã GD')
    tong_thu = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='Số tiền thu')
    don_ban = models.ForeignKey(DonBan, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Đơn bán hàng')
    ghi_chu = models.TextField(blank=True)
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu thu tiền'
        ordering = ['-ngay_thu']

    def __str__(self):
        return f"{self.so_phieu} - {self.khach_hang.ten_kh}"


class PhieuTraHang(models.Model):
    HINH_THUC_HOAN = [
        ('tien_mat', 'Hoàn tiền mặt'),
        ('bu_tru_no', 'Bù trừ công nợ'),
        ('doi_hang', 'Đổi hàng khác'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu trả')
    ngay_tra = models.DateField(default=datetime.date.today, verbose_name='Ngày trả')
    don_ban_goc = models.ForeignKey(DonBan, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Đơn bán gốc')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Khách hàng')
    ly_do_tra = models.CharField(max_length=200, verbose_name='Lý do trả hàng')
    hinh_thuc_hoan = models.CharField(max_length=20, choices=HINH_THUC_HOAN, default='tien_mat')
    tong_tien_hoan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                          verbose_name='Tổng tiền hoàn')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu trả hàng'
        ordering = ['-ngay_tra']


class PhieuTraHang_CT(models.Model):
    phieu_tra = models.ForeignKey(PhieuTraHang, on_delete=models.CASCADE,
                                   related_name='chi_tiet')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT)
    so_luong = models.IntegerField()
    don_gia = models.DecimalField(max_digits=18, decimal_places=0)
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    def save(self, *args, **kwargs):
        self.thanh_tien = self.so_luong * self.don_gia
        super().save(*args, **kwargs)
