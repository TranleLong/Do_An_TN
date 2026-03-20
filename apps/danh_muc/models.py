"""
Models cho app Danh Mục: KhachHang, NhaCungCap, BangGia
"""
from django.db import models


class NhomKhachHang(models.Model):
    ten_nhom = models.CharField(max_length=100, verbose_name='Tên nhóm KH')

    class Meta:
        verbose_name = 'Nhóm khách hàng'

    def __str__(self):
        return self.ten_nhom


class KhachHang(models.Model):
    LOAI_KH = [
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp'),
        ('gara', 'Gara/Xưởng'),
    ]
    ma_kh = models.CharField(max_length=20, unique=True, verbose_name='Mã KH')
    ten_kh = models.CharField(max_length=200, verbose_name='Tên khách hàng')
    loai_kh = models.CharField(max_length=20, choices=LOAI_KH, default='ca_nhan',
                                verbose_name='Loại KH')
    nhom_kh = models.ForeignKey(NhomKhachHang, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Nhóm KH')
    ma_so_thue = models.CharField(max_length=20, blank=True, verbose_name='MST')
    dia_chi = models.CharField(max_length=300, blank=True, verbose_name='Địa chỉ')
    so_dien_thoai = models.CharField(max_length=15, verbose_name='SĐT')
    email = models.EmailField(blank=True, verbose_name='Email')
    han_muc_cong_no = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                           verbose_name='Hạn mức công nợ')
    so_ngay_no_max = models.IntegerField(default=0, verbose_name='Số ngày nợ tối đa')
    chiet_khau_mac_dinh = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                               verbose_name='CK mặc định (%)')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    trang_thai = models.BooleanField(default=True, verbose_name='Hoạt động')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Khách hàng'
        verbose_name_plural = 'Danh sách khách hàng'
        ordering = ['ma_kh']

    def __str__(self):
        return f"{self.ma_kh} - {self.ten_kh}"

    def get_cong_no(self):
        from apps.ban_hang.models import DonBan
        from django.db.models import Sum
        total = DonBan.objects.filter(
            khach_hang=self, trang_thai='da_xac_nhan'
        ).aggregate(no=Sum('con_no'))['no']
        return total or 0


class NhaCungCap(models.Model):
    LOAI_NCC = [
        ('nha_sx', 'Nhà sản xuất'),
        ('dai_ly', 'Đại lý phân phối'),
        ('nhap_khau', 'Nhập khẩu'),
    ]
    ma_ncc = models.CharField(max_length=20, unique=True, verbose_name='Mã NCC')
    ten_ncc = models.CharField(max_length=200, verbose_name='Tên nhà cung cấp')
    loai_ncc = models.CharField(max_length=20, choices=LOAI_NCC, default='dai_ly',
                                 verbose_name='Loại NCC')
    ma_so_thue = models.CharField(max_length=20, blank=True, verbose_name='MST')
    dia_chi = models.CharField(max_length=300, blank=True, verbose_name='Địa chỉ')
    so_dien_thoai = models.CharField(max_length=15, blank=True, verbose_name='SĐT')
    email = models.EmailField(blank=True, verbose_name='Email')
    nguoi_lien_he = models.CharField(max_length=100, blank=True, verbose_name='Người liên hệ')
    so_tk_ngan_hang = models.CharField(max_length=50, blank=True, verbose_name='Số TK NH')
    ngan_hang = models.CharField(max_length=100, blank=True, verbose_name='Ngân hàng')
    so_ngay_thanh_toan = models.IntegerField(default=30, verbose_name='Số ngày TT')
    trang_thai = models.BooleanField(default=True, verbose_name='Hoạt động')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Nhà cung cấp'
        verbose_name_plural = 'Danh sách nhà cung cấp'
        ordering = ['ma_ncc']

    def __str__(self):
        return f"{self.ma_ncc} - {self.ten_ncc}"

    def get_cong_no(self):
        from apps.mua_hang.models import HoaDonMuaVao
        from django.db.models import Sum
        total = HoaDonMuaVao.objects.filter(
            nha_cung_cap=self
        ).aggregate(no=Sum('con_no'))['no']
        return total or 0
