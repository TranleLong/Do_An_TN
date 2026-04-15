import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from apps.danh_muc.models import HangHoa, KhachHang, Kho, NhomHang
from apps.so_cai.periods import AccountingPeriodLockMixin


class DonBan(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_chung_tu'
    accounting_period_label = 'đơn bán hàng'

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
        ('1', '1 - Lập chứng từ'),
        ('2', '2 - Chờ duyệt'),
        ('3', '3 - Duyệt'),
        ('4', '4 - Treo'),
    ]
    so_don = models.CharField(max_length=30, unique=True, verbose_name='Số đơn bán')
    ngay_chung_tu = models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ')
    ngay_ban = models.DateField(default=datetime.date.today, verbose_name='Ngày bán')
    loai_ban = models.CharField(max_length=20, choices=LOAI_BAN, default='ban_le',
                                 verbose_name='Loại bán')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Khách hàng')
    ten_kh = models.CharField(max_length=200, blank=True, verbose_name='Tên KH')
    sdt_kh = models.CharField(max_length=15, blank=True, verbose_name='SĐT KH')
    dia_chi_kh = models.CharField(max_length=300, blank=True, verbose_name='Địa chỉ KH')
    mst_kh = models.CharField(max_length=20, blank=True, verbose_name='MST KH')
    nguoi_mua_hang = models.CharField(max_length=120, blank=True, verbose_name='Người mua hàng')
    ma_nv_ban_hang = models.CharField(max_length=30, blank=True, verbose_name='Mã nhân viên bán hàng')
    xe_kh = models.CharField(max_length=100, blank=True, verbose_name='Xe KH')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Kho xuất')
    nhan_vien_ban = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                       verbose_name='Nhân viên bán')
    phuong_thuc_tt = models.CharField(max_length=20, choices=PHUONG_THUC_TT,
                                       default='tien_mat', verbose_name='PTTT')
    tong_tien_hang = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tong_so_luong = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Tổng số lượng')
    chiet_khau_dh = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                         verbose_name='Chiết khấu đơn hàng')
    ma_ngoai_te = models.CharField(max_length=10, default='VND', verbose_name='Mã ngoại tệ')
    ty_gia = models.DecimalField(max_digits=18, decimal_places=4, default=1, verbose_name='Tỷ giá')
    tong_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tong_thanh_toan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                           verbose_name='Tổng thanh toán')
    da_thu = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                  verbose_name='Đã thu')
    con_no = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                  verbose_name='Còn nợ')
    han_thanh_toan = models.DateField(null=True, blank=True, verbose_name='Hạn thanh toán')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1',
                                   verbose_name='Trạng thái')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ban_hang_donban'
        verbose_name = 'Đơn bán hàng'
        verbose_name_plural = 'Đơn bán hàng'
        ordering = ['-ngay_chung_tu', '-ngay_ban', '-ngay_tao']

    def __str__(self):
        return f"{self.so_don} - {self.ten_kh or 'Khách lẻ'}"

    def tinh_tong(self):
        tong_hang = sum(ct.thanh_tien for ct in self.chi_tiet.all())
        tong_thue = sum(ct.tien_thue for ct in self.chi_tiet.all())
        tong_so_luong = sum(Decimal(ct.so_luong or 0) for ct in self.chi_tiet.all())
        self.tong_tien_hang = tong_hang
        self.tong_thue = tong_thue
        self.tong_so_luong = tong_so_luong
        self.tong_thanh_toan = tong_hang + tong_thue - self.chiet_khau_dh
        self.con_no = self.tong_thanh_toan - self.da_thu
        self.save(update_fields=['tong_tien_hang', 'tong_thue', 'tong_so_luong', 'tong_thanh_toan', 'con_no'])

    def xac_nhan_don_ban(self):
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
    ngay_giao = models.DateField(default=datetime.date.today, verbose_name='Ngày giao')
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                      verbose_name='Thành tiền')
    tien_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Tiền thuế')
    gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                   verbose_name='Giá vốn')
    loi_nhuan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                     verbose_name='Lợi nhuận')

    class Meta:
        db_table = 'ban_hang_donban_ct'
        verbose_name = 'Chi tiết đơn bán'

    def save(self, *args, **kwargs):
        ck = self.don_gia * self.chiet_khau / 100
        gia_sau_ck = (self.don_gia - ck) * self.so_luong
        self.tien_thue = round(gia_sau_ck * self.thue_vat / 100, 0)
        self.thanh_tien = round(gia_sau_ck, 0)
        super().save(*args, **kwargs)


class PhieuThu(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_thu'
    accounting_period_label = 'phiếu thu'

    HINH_THUC = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
    ]
    TRANG_THAI = [
        ('1', '1 - Lập chứng từ'),
        ('2', '2 - Chuyển sổ cái'),
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
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1',
                                   verbose_name='Trạng thái')
    ghi_chu = models.TextField(blank=True)
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ban_hang_phieuthu'
        verbose_name = 'Phiếu thu tiền'
        ordering = ['-ngay_thu']

    def __str__(self):
        return f"{self.so_phieu} - {self.khach_hang.ten_kh}"


class CongNoCanhBaoConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cong_no_canh_bao_config')
    bat_canh_bao_qua_han = models.BooleanField(default=True, verbose_name='Bật cảnh báo nợ quá hạn')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ban_hang_congno_canhbao_config'
        verbose_name = 'Thiết lập cảnh báo công nợ'
        verbose_name_plural = 'Thiết lập cảnh báo công nợ'

    def __str__(self):
        return f"{self.user.username} - {'Bật' if self.bat_canh_bao_qua_han else 'Tắt'}"


class PhieuTraHang(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_hach_toan'
    accounting_period_label = 'phiếu đổi trả'

    HINH_THUC_XU_LY = [
        ('doi_hang', 'Đổi hàng'),
        ('tra_hang', 'Trả hàng'),
    ]
    HINH_THUC_HOAN = [
        ('1', '1 - Hoàn tiền mặt'),
        ('2', '2 - Bù trừ công nợ'),
        ('3', '3 - Đổi hàng khác'),
    ]
    TRANG_THAI = [
        ('1', '1 - Lập chứng từ'),
        ('2', '2 - Hoàn tất'),
    ]
    so_phieu = models.CharField(max_length=30, unique=True, verbose_name='Số phiếu trả')
    ngay_lap = models.DateField(default=datetime.date.today, verbose_name='Ngày lập')
    ngay_hach_toan = models.DateField(default=datetime.date.today, verbose_name='Ngày hạch toán')
    ngay_tra = models.DateField(default=datetime.date.today, verbose_name='Ngày trả')
    hoa_don_goc = models.ForeignKey('HoaDonBan', on_delete=models.PROTECT, null=True, blank=True,
                                     related_name='phieu_doi_tra', verbose_name='Hóa đơn gốc')
    don_ban_goc = models.ForeignKey(DonBan, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Đơn bán gốc')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Khách hàng')
    tk_no = models.CharField(max_length=20, default='131', verbose_name='TK nợ')
    tk_co = models.CharField(max_length=20, default='131', verbose_name='TK có')
    dien_giai = models.TextField(blank=True, verbose_name='Diễn giải')
    hinh_thuc_xu_ly = models.CharField(max_length=20, choices=HINH_THUC_XU_LY, default='tra_hang', verbose_name='Hình thức')
    ly_do_tra = models.CharField(max_length=200, verbose_name='Lý do trả hàng')
    hinh_thuc_hoan = models.CharField(max_length=20, choices=HINH_THUC_HOAN, default='1')
    tong_tien_tra = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng tiền hàng trả')
    tong_tien_doi = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng tiền hàng đổi')
    tong_tien_hoan = models.DecimalField(max_digits=18, decimal_places=0, default=0,
                                          verbose_name='Tổng tiền hoàn')
    chenh_lech_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Chênh lệch tiền')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1', verbose_name='Trạng thái')
    da_cap_nhat_kho_cong_no = models.BooleanField(default=False, verbose_name='Đã cập nhật kho/công nợ')
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ban_hang_phieutrahang'
        verbose_name = 'Phiếu trả hàng'
        ordering = ['-ngay_tra']


class PhieuTraHang_CT(models.Model):
    phieu_tra = models.ForeignKey(PhieuTraHang, on_delete=models.CASCADE,
                                   related_name='chi_tiet')
    hoa_don_ct_goc = models.ForeignKey('HoaDonBan_CT', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='chi_tiet_doi_tra')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Kho xử lý')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT)
    so_luong = models.IntegerField()
    don_gia = models.DecimalField(max_digits=18, decimal_places=0)
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    loai_hang_tra = models.CharField(max_length=20, choices=[('binh_thuong', 'Hàng bình thường'), ('hang_loi', 'Hàng lỗi')], default='binh_thuong')
    hang_hoa_doi = models.ForeignKey(HangHoa, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='chi_tiet_hang_doi')
    so_luong_doi = models.IntegerField(default=0)
    gia_ban_doi = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tien_doi = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    class Meta:
        db_table = 'ban_hang_phieutrahang_ct'

    def save(self, *args, **kwargs):
        self.thanh_tien = self.so_luong * self.don_gia
        self.tien_doi = self.so_luong_doi * self.gia_ban_doi
        super().save(*args, **kwargs)


class PhieuGiaBan(models.Model):
    """Phiếu giá bán - định mức giá theo nhóm hàng"""
    TRANG_THAI_DUYET = [
        ('0', 'Không sử dụng'),
        ('1', 'Sử dụng'),
    ]
    LOAI_TIEN_TE = [
        ('VND', 'VND'),
        ('USD', 'USD'),
    ]

    ma_phieu = models.CharField(max_length=30, unique=True, verbose_name='Mã phiếu giá bán')
    ngay_lap = models.DateField(default=datetime.date.today, verbose_name='Ngày lập')
    ngay_hieu_luc = models.DateField(verbose_name='Ngày hiệu lực')
    nguoi_lap = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='phieu_gia_ban_lap', verbose_name='Người lập')
    nhom_hang = models.ForeignKey(NhomHang, on_delete=models.PROTECT, verbose_name='Nhóm hàng')
    bien_do_loi_nhuan = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name='Biên độ lợi nhuận (%)')
    loai_tien_te = models.CharField(max_length=10, choices=LOAI_TIEN_TE, default='VND', verbose_name='Loại tiền tệ')
    trang_thai_duyet = models.CharField(max_length=20, choices=TRANG_THAI_DUYET, default='1', verbose_name='Trạng thái')
    ghi_chu = models.TextField(blank=True, verbose_name='Ghi chú')
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'ban_hang_phieu_gia_ban'
        verbose_name = 'Phiếu giá bán'
        ordering = ['-ngay_lap', '-ngay_tao']

    def __str__(self):
        return self.ma_phieu


class PhieuGiaBan_CT(models.Model):
    """Chi tiết phiếu giá bán"""
    phieu = models.ForeignKey(PhieuGiaBan, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name='Phiếu giá bán')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Mặt hàng')
    gia_von = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Giá vốn')
    gia_ban_chuan = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Giá bán chuẩn')

    class Meta:
        db_table = 'ban_hang_phieu_gia_ban_ct'
        verbose_name = 'Chi tiết phiếu giá bán'
        unique_together = ['phieu', 'hang_hoa']

    def __str__(self):
        return f"{self.phieu.ma_phieu} - {self.hang_hoa.ma_hang}"


class PhieuGiaBanChietKhau(models.Model):
    """Bảng chiết khấu theo số lượng"""
    phieu = models.ForeignKey(PhieuGiaBan, on_delete=models.CASCADE, related_name='bang_chiet_khau', verbose_name='Phiếu giá bán')
    tu_so_luong = models.IntegerField(verbose_name='Từ số lượng')
    den_so_luong = models.IntegerField(verbose_name='Đến số lượng')
    phan_tram_chiet_khau = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='% chiết khấu')

    class Meta:
        db_table = 'ban_hang_phieu_gia_ban_ck'
        verbose_name = 'Bảng chiết khấu'
        ordering = ['tu_so_luong']

    def __str__(self):
        return f"{self.phieu.ma_phieu}: {self.tu_so_luong}-{self.den_so_luong}"


class HoaDonBan(AccountingPeriodLockMixin, models.Model):
    accounting_period_date_field = 'ngay_hach_toan'
    accounting_period_label = 'hóa đơn bán hàng'

    MA_GIAO_DICH = [
        ('1', '1 - Hóa đơn kiêm phiếu xuất bán'),
        ('2', '2 - Hóa đơn'),
    ]
    MA_NGOAI_TE = [
        ('VND', 'VND'),
        ('USD', 'USD'),
    ]
    TRANG_THAI = [
        ('1', '1 - Lập chứng từ'),
        ('2', '2 - Chuyển sổ cái'),
    ]

    ma_giao_dich = models.CharField(max_length=5, choices=MA_GIAO_DICH, default='1', verbose_name='Mã giao dịch')
    so_hoa_don = models.CharField(max_length=30, unique=True, verbose_name='Số hóa đơn')
    ngay_lap = models.DateField(default=datetime.date.today, verbose_name='Ngày lập')
    ngay_hach_toan = models.DateField(default=datetime.date.today, verbose_name='Ngày hạch toán')
    ma_ngoai_te = models.CharField(max_length=10, choices=MA_NGOAI_TE, default='VND', verbose_name='Mã ngoại tệ')
    ty_gia = models.DecimalField(max_digits=18, decimal_places=4, default=1, verbose_name='Tỷ giá')
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.PROTECT, verbose_name='Khách hàng')
    ten_kh = models.CharField(max_length=200, blank=True, verbose_name='Tên khách')
    dia_chi = models.CharField(max_length=300, blank=True, verbose_name='Địa chỉ')
    so_dien_thoai = models.CharField(max_length=15, blank=True, verbose_name='Số điện thoại')
    mst = models.CharField(max_length=20, blank=True, verbose_name='MST')
    nguoi_mua_hang = models.CharField(max_length=120, blank=True, verbose_name='Người mua hàng')
    ma_nv_ban_hang = models.CharField(max_length=30, blank=True, verbose_name='Mã nhân viên bán hàng')
    tk_no = models.CharField(max_length=20, default='131', verbose_name='TK nợ')
    tk_co = models.CharField(max_length=20, default='511', verbose_name='TK có đối ứng')
    dien_giai = models.TextField(blank=True, verbose_name='Diễn giải')
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='1', verbose_name='Trạng thái')
    don_ban = models.ForeignKey(DonBan, on_delete=models.SET_NULL, null=True, blank=True, related_name='hoa_don_lien_ket', verbose_name='Đơn bán liên kết')

    tong_so_luong = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Tổng số lượng')
    tong_chiet_khau = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng chiết khấu')
    tien_hang = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tiền hàng')
    tong_tien_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng tiền thuế')
    tong_cong = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Tổng cộng')

    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hoa_don_ban_tao')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ban_hang_hoadonban'
        verbose_name = 'Hóa đơn bán hàng'
        verbose_name_plural = 'Hóa đơn bán hàng'
        ordering = ['-ngay_lap', '-id']

    def __str__(self):
        return self.so_hoa_don

    def tinh_tong(self):
        rows = self.chi_tiet.all()
        self.tong_so_luong = sum(Decimal(r.so_luong or 0) for r in rows)
        self.tong_chiet_khau = sum(Decimal(r.tien_chiet_khau or 0) for r in rows)
        self.tien_hang = sum(Decimal(r.tien_hang or 0) for r in rows)
        self.tong_tien_thue = sum(Decimal(r.tien_thue or 0) for r in rows)
        self.tong_cong = self.tien_hang + self.tong_tien_thue
        self.save(update_fields=['tong_so_luong', 'tong_chiet_khau', 'tien_hang', 'tong_tien_thue', 'tong_cong'])


class HoaDonBan_CT(models.Model):
    hoa_don = models.ForeignKey(HoaDonBan, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name='Hóa đơn')
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.PROTECT, verbose_name='Mã hàng')
    kho = models.ForeignKey(Kho, on_delete=models.PROTECT, verbose_name='Mã kho')
    so_luong = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Số lượng')
    gia_ban = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Giá bán')
    ty_le_chiet_khau = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Tỷ lệ chiết khấu (%)')
    thue_suat = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name='Thuế suất (%)')
    tk_thue = models.CharField(max_length=20, blank=True, verbose_name='TK thuế')
    tk_vat_tu = models.CharField(max_length=20, blank=True, verbose_name='TK vật tư')
    tk_gia_von = models.CharField(max_length=20, blank=True, verbose_name='TK giá vốn')
    tk_doanh_thu = models.CharField(max_length=20, blank=True, verbose_name='TK doanh thu')

    tien_chiet_khau = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tien_hang = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    tien_thue = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    thanh_tien = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    class Meta:
        db_table = 'ban_hang_hoadonban_ct'
        verbose_name = 'Chi tiết hóa đơn bán hàng'

    def save(self, *args, **kwargs):
        base = Decimal(self.so_luong or 0) * Decimal(self.gia_ban or 0)
        self.tien_chiet_khau = round(base * Decimal(self.ty_le_chiet_khau or 0) / Decimal('100'), 0)
        self.tien_hang = round(base - self.tien_chiet_khau, 0)
        self.tien_thue = round(self.tien_hang * Decimal(self.thue_suat or 0) / Decimal('100'), 0)
        self.thanh_tien = round(self.tien_hang + self.tien_thue, 0)
        super().save(*args, **kwargs)
