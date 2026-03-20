"""
Models cho app Core: Danh mục hàng hóa, Kho, Tồn kho
"""
from django.db import models
from django.utils import timezone


class NhomHang(models.Model):
    ma_nhom = models.CharField(max_length=20, unique=True, verbose_name='Mã nhóm')
    ten_nhom = models.CharField(max_length=100, verbose_name='Tên nhóm hàng')
    mo_ta = models.TextField(blank=True, verbose_name='Mô tả')

    class Meta:
        verbose_name = 'Nhóm hàng'
        verbose_name_plural = 'Nhóm hàng'
        ordering = ['ten_nhom']

    def __str__(self):
        return f"{self.ma_nhom} - {self.ten_nhom}"


class ThuongHieu(models.Model):
    ten = models.CharField(max_length=100, unique=True, verbose_name='Thương hiệu')
    nuoc_san_xuat = models.CharField(max_length=100, blank=True, verbose_name='Nước SX')

    class Meta:
        verbose_name = 'Thương hiệu'
        ordering = ['ten']

    def __str__(self):
        return self.ten


class DonViTinh(models.Model):
    ten = models.CharField(max_length=50, unique=True, verbose_name='ĐVT')

    class Meta:
        verbose_name = 'Đơn vị tính'

    def __str__(self):
        return self.ten


class HangHoa(models.Model):
    TRANG_THAI = [
        ('dang_ban', 'Đang bán'),
        ('ngung_ban', 'Ngừng bán'),
    ]
    ma_hang = models.CharField(max_length=20, unique=True, verbose_name='Mã hàng')
    ten_hang = models.CharField(max_length=200, verbose_name='Tên hàng hóa')
    nhom_hang = models.ForeignKey(NhomHang, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='Nhóm hàng')
    thuong_hieu = models.ForeignKey(ThuongHieu, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Thương hiệu')
    don_vi_tinh = models.ForeignKey(DonViTinh, on_delete=models.SET_NULL, null=True,
                                     verbose_name='ĐVT')
    xe_tuong_thich = models.CharField(max_length=500, blank=True, verbose_name='Xe tương thích')
    barcode = models.CharField(max_length=50, blank=True, verbose_name='Barcode')
    gia_ban_le = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                      verbose_name='Giá bán lẻ')
    gia_ban_buon = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                        verbose_name='Giá bán buôn')
    ton_toi_thieu = models.IntegerField(default=0, verbose_name='Tồn tối thiểu')
    ton_toi_da = models.IntegerField(default=0, verbose_name='Tồn tối đa')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='dang_ban',
                                   verbose_name='Trạng thái')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hàng hóa'
        verbose_name_plural = 'Danh sách hàng hóa'
        ordering = ['ma_hang']

    def __str__(self):
        return f"{self.ma_hang} - {self.ten_hang}"

    def get_ton_kho(self):
        from apps.kho.models import TonKho
        total = TonKho.objects.filter(hang_hoa=self).aggregate(
            total=models.Sum('so_luong'))['total']
        return total or 0

    def get_gia_von(self):
        from apps.kho.models import TonKho
        tk = TonKho.objects.filter(hang_hoa=self).first()
        return tk.gia_von_tb if tk else 0


class Kho(models.Model):
    ma_kho = models.CharField(max_length=10, unique=True, verbose_name='Mã kho')
    ten_kho = models.CharField(max_length=100, verbose_name='Tên kho')
    dia_chi = models.CharField(max_length=200, blank=True, verbose_name='Địa chỉ')
    trang_thai = models.BooleanField(default=True, verbose_name='Hoạt động')

    class Meta:
        verbose_name = 'Kho'
        ordering = ['ma_kho']

    def __str__(self):
        return f"{self.ma_kho} - {self.ten_kho}"


class ViTriKho(models.Model):
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name='Kho')
    ma_vi_tri = models.CharField(max_length=20, verbose_name='Mã vị trí')
    mo_ta = models.CharField(max_length=100, blank=True, verbose_name='Mô tả')

    class Meta:
        verbose_name = 'Vị trí kho'
        unique_together = ['kho', 'ma_vi_tri']

    def __str__(self):
        return f"{self.kho.ma_kho} - {self.ma_vi_tri}"
