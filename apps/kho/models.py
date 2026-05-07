"""Models dữ liệu app Kho (chỉ khai báo cấu trúc bảng)."""
import datetime

from django.contrib.auth.models import User
from django.db import models

from apps.danh_muc.models import HangHoa, Kho, NhaCungCap, NhomHang, ViTriKho
from apps.so_cai.periods import AccountingPeriodLockMixin


class TonKho(models.Model):
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.CASCADE, verbose_name='Hàng hóa')
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name='Kho')
    so_luong = models.IntegerField(default=0, verbose_name='Số lượng tồn')
    so_luong_loi = models.IntegerField(default=0, verbose_name='Số lượng hàng lỗi')
    gia_von_tb = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Giá vốn TB')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kho_tonkho'
        unique_together = ['hang_hoa', 'kho']
        verbose_name = 'Tồn kho'

    def __str__(self):
        return f"{self.hang_hoa.ma_hang} | {self.kho.ma_kho} | SL: {self.so_luong}"


class MucTonKho(models.Model):
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.CASCADE, verbose_name='Hàng hóa')
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name='Kho áp dụng')
    ton_toi_thieu = models.IntegerField(default=0, verbose_name='Tồn tối thiểu')
    ton_toi_da = models.IntegerField(null=True, blank=True, verbose_name='Tồn tối đa')
    ghi_chu = models.CharField(max_length=255, blank=True, verbose_name='Ghi chú')
    nguoi_cap_nhat = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name='Người cập nhật')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kho_muctonkho'
        unique_together = ['hang_hoa', 'kho']
        verbose_name = 'Mức tồn kho'
        verbose_name_plural = 'Mức tồn kho'

    def __str__(self):
        return f"{self.hang_hoa.ma_hang} - {self.kho.ma_kho}"


class TonKhoViTri(models.Model):
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.CASCADE, verbose_name='Hàng hóa')
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name='Kho')
    vi_tri = models.ForeignKey(ViTriKho, on_delete=models.CASCADE, verbose_name='Vị trí kho')
    so_luong = models.IntegerField(default=0, verbose_name='Số lượng tại vị trí')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kho_tonkho_vitri'
        unique_together = ['hang_hoa', 'vi_tri']
        verbose_name = 'Tồn kho theo vị trí'

    def __str__(self):
        return f"{self.hang_hoa.ma_hang} | {self.vi_tri.ma_vi_tri} | SL: {self.so_luong}"


class PhieuNhap(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_hach_toan'
    accounting_period_label = 'phiếu nhập kho'

    LOAI_NHAP = [
        ('1', 'Mua nhà cung cấp'),
        ('2', 'Khách hàng trả hàng'),
        ('3', 'Nhập chênh lệch kiểm kê'),
    ]
    TRANG_THAI = [
        ('1', '1 - Lập phiếu'),
        ('2', '2 - Sổ kho'),
        ('3', '3 - Sổ cái'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu nhập')
    ngay_lap = models.DateField(default=datetime.date.today, verbose_name='Ngày lập')
    ngay_hach_toan = models.DateField(default=datetime.date.today, verbose_name='Ngày hạch toán')
    ngay_chung_tu = models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ')
    ngay_nhap = models.DateField(default=datetime.date.today, verbose_name='Ngày nhập')
    loai_nhap = models.CharField(max_length=20, choices=LOAI_NHAP, default='1',
                                  verbose_name='Loại nhập')
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name='Nhà cung cấp')
    so_hd_ncc = models.CharField(max_length=50, blank=True, verbose_name='Số HĐ NCC')
    ngay_hd_ncc = models.DateField(null=True, blank=True, verbose_name='Ngày HĐ NCC')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho nhập')
    tong_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Tổng tiền')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1',
                                   verbose_name='Trạng thái')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   verbose_name='Người tạo')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kho_phieunhap'
        verbose_name = 'Phiếu nhập kho'
        verbose_name_plural = 'Phiếu nhập kho'
        ordering = ['-ngay_hach_toan', '-ngay_lap', '-ngay_tao']

    def __str__(self):
        return f"{self.so_phieu} ({self.get_trang_thai_display()})"

    def tinh_tong(self):
        tong = sum(ct.thanh_tien for ct in self.chi_tiet.all())
        self.tong_tien = tong
        self.save(update_fields=['tong_tien'])
        return tong

    def xac_nhan_nhap_kho(self):
        """
        BR12.x.5: Kiểm tra không có chênh lệch kiểm kê chưa xử lý trước khi nhập kho.
        """
        if self.trang_thai != '1':
            return False
        
        # BR12.x.5: Kiểm tra hàng hóa có chênh lệch kiểm kê chưa xử lý
        hang_ids = list(self.chi_tiet.values_list('hang_hoa_id', flat=True))
        if hang_ids:
            # Import tại đây để tránh circular import
            from apps.kho.views import _check_kiem_ke_diff
            conflicted = _check_kiem_ke_diff(self.kho_id, hang_ids)
            if conflicted:
                return False  # Không cho xác nhận nếu có chênh lệch chưa xử lý

        for ct in self.chi_tiet.all():
            ton_kho, _ = TonKho.objects.get_or_create(
                hang_hoa=ct.hang_hoa,
                kho=self.kho,
                defaults={'so_luong': 0, 'gia_von_tb': 0},
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

        self.trang_thai = '2'
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
    tk_no = models.CharField(max_length=20, blank=True, verbose_name='TK Nợ')
    tk_co = models.CharField(max_length=20, blank=True, verbose_name='TK Có')

    class Meta:
        db_table = 'kho_phieunhap_ct'
        verbose_name = 'Chi tiết phiếu nhập'

    def save(self, *args, **kwargs):
        ck = self.don_gia * self.chiet_khau / 100
        self.thue_vat = 0
        self.thanh_tien = round((self.don_gia - ck) * self.so_luong_nhan, 0)
        super().save(*args, **kwargs)

class PhieuNhap_CT_Allocation(models.Model):
    phieu_nhap_ct = models.ForeignKey(PhieuNhap_CT, on_delete=models.CASCADE, related_name='allocations')
    vi_tri = models.ForeignKey(ViTriKho, on_delete=models.CASCADE, verbose_name='Vị trí ô kệ')
    so_luong = models.IntegerField(default=0, verbose_name='Số lượng phân bổ')
    ma_vi_tri = models.CharField(max_length=50, verbose_name='Mã vị trí', default='')

    class Meta:
        db_table = 'kho_phieunhap_ct_allocation'
        verbose_name = 'Phân bổ vị trí chi tiết'



class PhieuXuat(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_hach_toan'
    accounting_period_label = 'phiếu xuất kho'

    LOAI_XUAT = [
        ('ban_hang', 'Xuất bán hàng'),
        ('tra_ncc', 'Trả nhà cung cấp'),
        ('noi_bo', 'Xuất nội bộ'),
        ('hu_hong', 'Hư hỏng / Hao hụt'),
        ('kiem_ke', 'Xuất chênh lệch kiểm kê'),
    ]
    TRANG_THAI = [
        ('1', '1 - Lập phiếu'),
        ('2', '2 - Sổ kho'),
        ('3', '3 - Sổ cái'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu xuất')
    ngay_lap = models.DateField(default=datetime.date.today, verbose_name='Ngày lập')
    ngay_hach_toan = models.DateField(default=datetime.date.today, verbose_name='Ngày hạch toán')
    ngay_chung_tu = models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ')
    ngay_xuat = models.DateField(default=datetime.date.today, verbose_name='Ngày xuất')
    loai_xuat = models.CharField(max_length=20, choices=LOAI_XUAT, default='ban_hang',
                                  verbose_name='Loại xuất')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho xuất')
    tong_gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                        verbose_name='Tổng giá vốn')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1',
                                   verbose_name='Trạng thái')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   verbose_name='Người tạo')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kho_phieuxuat'
        verbose_name = 'Phiếu xuất kho'
        ordering = ['-ngay_hach_toan', '-ngay_lap', '-ngay_tao']

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
    gia_xuat = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Giá xuất')
    tong_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng tiền')

    def save(self, *args, **kwargs):
        # Nếu giá xuất chưa có, mặc định lấy giá vốn
        if not self.gia_xuat or self.gia_xuat == 0:
            self.gia_xuat = self.gia_von
        self.tong_tien = (self.so_luong or 0) * (self.gia_xuat or 0)
        super().save(*args, **kwargs)
    tk_no = models.CharField(max_length=20, blank=True, verbose_name='TK Nợ')
    tk_co = models.CharField(max_length=20, blank=True, verbose_name='TK Có')

    class Meta:
        db_table = 'kho_phieuxuat_ct'
        verbose_name = 'Chi tiết phiếu xuất'


class KiemKe(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_kiem_ke'
    accounting_period_label = 'phiếu kiểm kê'

    TRANG_THAI = [
        ('1', '1 - Chờ kiểm kê'),
        ('2', '2 - Chờ điều chỉnh'),
        ('3', '3 - Hoàn thành'),
    ]
    ma_phieu = models.CharField(max_length=30, unique=True, blank=True, verbose_name='Mã phiếu kiểm kê')
    ngay_kiem_ke = models.DateField(default=datetime.date.today, verbose_name='Ngày kiểm kê')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho')
    nhom_hang = models.ForeignKey(NhomHang, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Loại hàng hóa kiểm kê')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Hàng hóa kiểm kê')
    khu_vuc = models.CharField(max_length=120, blank=True, verbose_name='Khu vực kiểm kê')
    vi_tri_hang_loi = models.ForeignKey(
        ViTriKho,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kiem_ke_hang_loi',
        verbose_name='Vị trí hàng lỗi',
    )
    nguoi_kiem = models.CharField(max_length=100, blank=True, verbose_name='Người kiểm kê')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1')
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kho_kiemke'
        verbose_name = 'Phiếu kiểm kê'
        ordering = ['-ngay_kiem_ke']

    def __str__(self):
        return f"{self.ma_phieu or 'KK'} - {self.kho.ten_kho} - {self.ngay_kiem_ke}"


class KiemKe_CT(models.Model):
    TINH_TRANG = [
        ('tot_100', 'Tốt 100%'),
        ('hu_hong', 'Hư hỏng'),
        ('thieu_hang', 'Thiếu hàng'),
    ]
    kiem_ke = models.ForeignKey(KiemKe, on_delete=models.CASCADE, related_name='chi_tiet')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong_so_sach = models.IntegerField(verbose_name='SL sổ sách')
    so_luong_thuc_te = models.IntegerField(verbose_name='SL thực tế')
    so_luong_loi = models.IntegerField(default=0, verbose_name='SL hàng lỗi')
    chenh_lech = models.IntegerField(default=0, verbose_name='Chênh lệch')
    tinh_trang = models.CharField(max_length=20, choices=TINH_TRANG, default='tot_100', verbose_name='Tình trạng')
    ly_do = models.CharField(max_length=200, blank=True, verbose_name='Lý do chênh lệch')

    class Meta:
        db_table = 'kho_kiemke_ct'

    def save(self, *args, **kwargs):
        self.chenh_lech = self.so_luong_thuc_te - self.so_luong_so_sach
        super().save(*args, **kwargs)


class PhieuDieuChinhKiemKe(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_dieu_chinh'
    accounting_period_label = 'phiếu điều chỉnh kiểm kê'

    TRANG_THAI = [
        ('1', '1 - Chờ duyệt'),
        ('2', '2 - Đã duyệt'),
    ]

    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Mã phiếu điều chỉnh')
    kiem_ke = models.OneToOneField(KiemKe, on_delete=models.PROTECT, related_name='phieu_dieu_chinh')
    ngay_dieu_chinh = models.DateField(default=datetime.date.today, verbose_name='Ngày điều chỉnh')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho')
    nguoi_lap = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Người lập')
    ly_do = models.CharField(max_length=255, verbose_name='Lý do điều chỉnh')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1', verbose_name='Trạng thái')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kho_phieudieuchinh_kiemke'
        verbose_name = 'Phiếu điều chỉnh kiểm kê'
        ordering = ['-ngay_dieu_chinh', '-id']

    def __str__(self):
        return self.so_phieu


class PhieuDieuChinhKiemKe_CT(models.Model):
    phieu = models.ForeignKey(PhieuDieuChinhKiemKe, on_delete=models.CASCADE, related_name='chi_tiet')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Hàng hóa')
    so_luong_he_thong = models.IntegerField(verbose_name='SL hệ thống')
    so_luong_thuc_te = models.IntegerField(verbose_name='SL thực tế')
    so_luong_loi = models.IntegerField(default=0, verbose_name='SL hàng lỗi')
    chenh_lech = models.IntegerField(verbose_name='Chênh lệch')
    ly_do = models.CharField(max_length=255, blank=True, verbose_name='Lý do điều chỉnh')

    class Meta:
        db_table = 'kho_phieudieuchinh_kiemke_ct'
        verbose_name = 'Chi tiết phiếu điều chỉnh kiểm kê'
