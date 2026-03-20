"""
Models cho app Mua Hàng: DonMua, HoaDonMuaVao, PhieuChi
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import HangHoa, Kho
from apps.danh_muc.models import NhaCungCap
import datetime


class DonMua(models.Model):
    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('nhan_1_phan', 'Nhận một phần'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Đã hủy'),
    ]
    so_don = models.CharField(max_length=30, unique=True, verbose_name='Số đơn mua')
    ngay_dat = models.DateField(default=datetime.date.today, verbose_name='Ngày đặt')
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.PROTECT,
                                      verbose_name='Nhà cung cấp')
    ngay_giao_dk = models.DateField(null=True, blank=True, verbose_name='Ngày giao dự kiến')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho nhận')
    ly_do = models.CharField(max_length=200, blank=True, verbose_name='Lý do đặt hàng')
    tong_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Tổng tiền')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='nhap',
                                   verbose_name='Trạng thái')
    nguoi_lap = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='don_mua_lap', verbose_name='Người lập')
    nguoi_duyet = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='don_mua_duyet', verbose_name='Người duyệt')
    ngay_duyet = models.DateTimeField(null=True, blank=True, verbose_name='Ngày duyệt')
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Đơn đặt mua hàng'
        ordering = ['-ngay_dat', '-ngay_tao']

    def __str__(self):
        return f"{self.so_don} - {self.nha_cung_cap.ten_ncc}"

    def tinh_tong(self):
        tong = sum(ct.thanh_tien for ct in self.chi_tiet.all())
        self.tong_tien = tong
        self.save(update_fields=['tong_tien'])


class DonMua_CT(models.Model):
    don_mua = models.ForeignKey(DonMua, on_delete=models.CASCADE,
                                 related_name='chi_tiet', verbose_name='Đơn mua')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong_dat = models.IntegerField(verbose_name='SL đặt')
    so_luong_da_nhan = models.IntegerField(default=0, verbose_name='SL đã nhận')
    don_gia = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='Đơn giá')
    thue_vat = models.DecimalField(max_digits=5, decimal_places=2, default=10,
                                    verbose_name='VAT (%)')
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    @property
    def con_can_nhan(self):
        return self.so_luong_dat - self.so_luong_da_nhan

    def save(self, *args, **kwargs):
        vat = self.don_gia * self.so_luong_dat * self.thue_vat / 100
        self.thanh_tien = round(self.don_gia * self.so_luong_dat + vat, 0)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Chi tiết đơn mua'


class HoaDonMuaVao(models.Model):
    TRANG_THAI = [
        ('chua_tt', 'Chưa thanh toán'),
        ('tt_1_phan', 'TT một phần'),
        ('da_tt', 'Đã thanh toán'),
    ]
    so_hoa_don = models.CharField(max_length=30, unique=True, verbose_name='Số HĐ mua vào')
    so_hd_ncc = models.CharField(max_length=50, blank=True, verbose_name='Số HĐ NCC')
    ngay_hd = models.DateField(default=datetime.date.today, verbose_name='Ngày HĐ')
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.PROTECT,
                                      verbose_name='Nhà cung cấp')
    don_mua = models.ForeignKey(DonMua, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Đơn mua liên kết')
    tong_tien_hang = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    thue_vat = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tong_thanh_toan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                           verbose_name='Tổng TT')
    da_thanh_toan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                         verbose_name='Đã TT')
    con_no = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                  verbose_name='Còn nợ')
    han_thanh_toan = models.DateField(null=True, blank=True, verbose_name='Hạn TT')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='chua_tt')
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hóa đơn mua vào'
        ordering = ['-ngay_hd']

    def __str__(self):
        return f"{self.so_hoa_don} - {self.nha_cung_cap.ten_ncc}"


class PhieuChi(models.Model):
    HINH_THUC = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu chi')
    ngay_chi = models.DateField(default=datetime.date.today, verbose_name='Ngày chi')
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.PROTECT,
                                      verbose_name='Nhà cung cấp')
    hinh_thuc = models.CharField(max_length=20, choices=HINH_THUC, default='tien_mat')
    so_tk_chi = models.CharField(max_length=100, blank=True, verbose_name='TK/NH chi')
    so_tham_chieu = models.CharField(max_length=100, blank=True, verbose_name='Mã GD')
    tong_chi = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='Số tiền chi')
    hoa_don_lien_ket = models.ForeignKey(HoaDonMuaVao, on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='Liên kết HĐ')
    ghi_chu = models.TextField(blank=True)
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phiếu chi tiền NCC'
        ordering = ['-ngay_chi']

    def __str__(self):
        return f"{self.so_phieu} - {self.nha_cung_cap.ten_ncc}"
