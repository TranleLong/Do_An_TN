"""Models dữ liệu app Danh mục (chỉ khai báo cấu trúc bảng)."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum


class NhomKhachHang(models.Model):
    ten_nhom = models.CharField(max_length=100, verbose_name="Tên nhóm khách hàng")

    class Meta:
        db_table = "danh_muc_nhomkhachhang"
        verbose_name = "Nhóm khách hàng"

    def __str__(self):
        return self.ten_nhom


class KhachHang(models.Model):
    LOAI_KH = [
        ("1", "Cá nhân"),
        ("2", "Doanh nghiệp"),
        ("3", "Khác"),
    ]

    ma_kh = models.CharField(max_length=20, unique=True, verbose_name="Mã khách hàng")
    ten_kh = models.CharField(max_length=200, verbose_name="Tên khách hàng")
    la_khach_hang = models.BooleanField(default=True, verbose_name="Khách hàng")
    la_nha_cung_cap = models.BooleanField(default=False, verbose_name="Nhà cung cấp")
    loai_kh = models.CharField(max_length=20, choices=LOAI_KH, default="1", verbose_name="Loại khách hàng")
    ma_so_thue = models.CharField(max_length=20, blank=True, verbose_name="Mã số thuế")
    dia_chi = models.CharField(max_length=300, blank=True, verbose_name="Địa chỉ")
    so_dien_thoai = models.CharField(max_length=15, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    han_muc_cong_no = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name="Hạn mức công nợ")
    so_ngay_no_max = models.IntegerField(default=0, verbose_name="Số ngày nợ tối đa")
    chiet_khau_mac_dinh = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Chiết khấu mặc định (%)")
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")
    trang_thai = models.BooleanField(default=True, verbose_name="Trạng thái")
    ngay_tao = models.DateTimeField(auto_now_add=True)

    nhom_kh = models.ForeignKey(
        NhomKhachHang,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Nhóm khách hàng",
    )

    class Meta:
        db_table = "danh_muc_khachhang"
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách khách hàng"
        ordering = ["ma_kh"]

    def __str__(self):
        return f"{self.ma_kh} - {self.ten_kh}"

    def get_cong_no(self):
        from apps.ban_hang.models import DonBan

        total = DonBan.objects.filter(khach_hang=self, trang_thai__in=["2", "3"]).aggregate(no=Sum("con_no"))["no"]
        return total or 0


class NhaCungCap(models.Model):
    LOAI_NCC = [
        ("nha_sx", "Nhà sản xuất"),
        ("dai_ly", "Đại lý phân phối"),
        ("nhap_khau", "Nhập khẩu"),
    ]

    ma_ncc = models.CharField(max_length=20, unique=True, verbose_name="Mã nhà cung cấp")
    ten_ncc = models.CharField(max_length=200, verbose_name="Tên nhà cung cấp")
    loai_ncc = models.CharField(max_length=20, choices=LOAI_NCC, default="dai_ly", verbose_name="Loại nhà cung cấp")
    ma_so_thue = models.CharField(max_length=20, blank=True, verbose_name="Mã số thuế")
    dia_chi = models.CharField(max_length=300, blank=True, verbose_name="Địa chỉ")
    so_dien_thoai = models.CharField(max_length=15, blank=True, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    nguoi_lien_he = models.CharField(max_length=100, blank=True, verbose_name="Người liên hệ")
    so_tk_ngan_hang = models.CharField(max_length=50, blank=True, verbose_name="Số tài khoản ngân hàng")
    ngan_hang = models.CharField(max_length=100, blank=True, verbose_name="Ngân hàng")
    so_ngay_thanh_toan = models.IntegerField(default=30, verbose_name="Số ngày thanh toán")
    trang_thai = models.BooleanField(default=True, verbose_name="Trạng thái")
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "danh_muc_nhacungcap"
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Danh sách nhà cung cấp"
        ordering = ["ma_ncc"]

    def __str__(self):
        return f"{self.ma_ncc} - {self.ten_ncc}"

    def get_cong_no(self):
        from apps.mua_hang.models import HoaDonMuaVao

        total = HoaDonMuaVao.objects.filter(nha_cung_cap=self).aggregate(no=Sum("con_no"))["no"]
        return total or 0


class NhomHang(models.Model):
    ma_nhom = models.CharField(max_length=20, unique=True, verbose_name="Mã nhóm")
    ten_nhom = models.CharField(max_length=100, verbose_name="Tên nhóm hàng")
    bien_do_loi_nhuan = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name="Biên độ lợi nhuận (%)")
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả")

    class Meta:
        db_table = "core_nhomhang"
        verbose_name = "Nhóm hàng"
        verbose_name_plural = "Nhóm hàng"
        ordering = ["ten_nhom"]

    def __str__(self):
        return f"{self.ma_nhom} - {self.ten_nhom}"


class ThuongHieu(models.Model):
    ten = models.CharField(max_length=100, unique=True, verbose_name="Thương hiệu")
    nuoc_san_xuat = models.CharField(max_length=100, blank=True, verbose_name="Nước sản xuất")

    class Meta:
        db_table = "core_thuonghieu"
        verbose_name = "Thương hiệu"
        ordering = ["ten"]

    def __str__(self):
        return self.ten


class DonViTinh(models.Model):
    ten = models.CharField(max_length=50, unique=True, verbose_name="Đơn vị tính")

    class Meta:
        db_table = "core_donvitinh"
        verbose_name = "Đơn vị tính"

    def __str__(self):
        return self.ten


class HangHoa(models.Model):
    TRANG_THAI = [
        ("dang_ban", "Đang bán"),
        ("ngung_ban", "Ngừng bán"),
    ]
    LOAI_O = [
        ("nho", "Nhỏ"),
        ("vua", "Vừa"),
        ("lon", "Lớn"),
        ("nang", "Nặng"),
        ("cong_kenh", "Cồng kềnh"),
    ]
    LOAI_LUU_TRU = [
        ("cai", "Cái"),
        ("hop", "Hộp"),
        ("khay", "Khay"),
        ("thung", "Thùng"),
        ("kien", "Kiện"),
        ("pack", "Pack"),
    ]

    ma_hang = models.CharField(max_length=20, unique=True, verbose_name="Mã hàng")
    ten_hang = models.CharField(max_length=200, verbose_name="Tên hàng hóa")
    xe_tuong_thich = models.CharField(max_length=500, blank=True, verbose_name="Xe tương thích")
    ton_toi_thieu = models.IntegerField(default=0, verbose_name="Tồn tối thiểu")
    ton_toi_da = models.IntegerField(default=0, verbose_name="Tồn tối đa")
    dai_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Dài (cm)")
    rong_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Rộng (cm)")
    cao_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cao (cm)")
    khoi_luong_kg = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Khối lượng (kg)")
    muc_chiem_cho = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name="Mức chiếm chỗ (1-50)",
    )
    loai_o_phu_hop = models.CharField(max_length=20, choices=LOAI_O, default="vua", verbose_name="Loại ô phù hợp")
    loai_luu_tru = models.CharField(max_length=20, choices=LOAI_LUU_TRU, default="cai", verbose_name="Loại lưu trữ")
    co_the_xep_chong = models.BooleanField(default=True, verbose_name="Có thể xếp chồng")
    so_luong_toi_da_moi_o = models.IntegerField(default=10, verbose_name="Số lượng tối đa mỗi ô")
    nha_cung_cap = models.ForeignKey(
        NhaCungCap,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Nhà cung cấp chính",
    )
    quy_cach_dong_goi = models.CharField(max_length=120, blank=True, verbose_name="Quy cách đóng gói")
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default="dang_ban", verbose_name="Trạng thái")
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")
    ngay_tao = models.DateTimeField(auto_now_add=True)

    nhom_hang = models.ForeignKey(NhomHang, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nhóm hàng")
    thuong_hieu = models.ForeignKey(ThuongHieu, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Thương hiệu")
    don_vi_tinh = models.ForeignKey(DonViTinh, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Đơn vị tính")

    class Meta:
        db_table = "core_hanghoa"
        verbose_name = "Hàng hóa"
        verbose_name_plural = "Danh sách hàng hóa"
        ordering = ["ma_hang"]
        constraints = [
            models.CheckConstraint(
                name="hanghoa_muc_chiem_cho_1_50",
                condition=models.Q(muc_chiem_cho__gte=1, muc_chiem_cho__lte=50),
            ),
        ]

    def __str__(self):
        return f"{self.ma_hang} - {self.ten_hang}"

    def get_ton_kho(self):
        from apps.kho.models import TonKho

        total = TonKho.objects.filter(hang_hoa=self).aggregate(total=Sum("so_luong"))["total"]
        return total or 0

    def get_gia_von(self):
        from apps.kho.models import TonKho

        tk = TonKho.objects.filter(hang_hoa=self).first()
        return tk.gia_von_tb if tk else 0


class Kho(models.Model):
    ma_kho = models.CharField(max_length=10, unique=True, verbose_name="Mã kho")
    ten_kho = models.CharField(max_length=100, verbose_name="Tên kho")
    dia_chi = models.CharField(max_length=200, blank=True, verbose_name="Địa chỉ")
    trang_thai = models.BooleanField(default=True, verbose_name="Hoạt động")

    class Meta:
        db_table = "core_kho"
        verbose_name = "Kho"
        ordering = ["ma_kho"]

    def __str__(self):
        return f"{self.ma_kho} - {self.ten_kho}"


class ViTriKho(models.Model):
    LOAI_O = [
        ("nho", "Nhỏ"),
        ("vua", "Vừa"),
        ("lon", "Lớn"),
        ("nang", "Nặng"),
        ("cong_kenh", "Cồng kềnh"),
    ]
    TRANG_THAI_O = [
        ("hoat_dong", "Hoạt động"),
        ("bao_tri", "Bảo trì"),
        ("khoa", "Khóa"),
    ]

    ma_vi_tri = models.CharField(max_length=20, verbose_name="Mã vị trí")
    mo_ta = models.CharField(max_length=100, blank=True, verbose_name="Mô tả")
    dai_cm = models.DecimalField(max_digits=10, decimal_places=2, default=60, verbose_name="Dài ô (cm)")
    rong_cm = models.DecimalField(max_digits=10, decimal_places=2, default=40, verbose_name="Rộng ô (cm)")
    cao_cm = models.DecimalField(max_digits=10, decimal_places=2, default=35, verbose_name="Cao ô (cm)")
    tai_trong_toi_da_kg = models.DecimalField(max_digits=10, decimal_places=3, default=30, verbose_name="Tải trọng tối đa (kg)")
    loai_o = models.CharField(max_length=20, choices=LOAI_O, default="vua", verbose_name="Loại ô")
    suc_chua_toi_da = models.IntegerField(default=50, verbose_name="Sức chứa tối đa")
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_O, default="hoat_dong", verbose_name="Trạng thái")
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name="Kho")

    class Meta:
        db_table = "core_vitrikho"
        verbose_name = "Vị trí kho"
        unique_together = ["kho", "ma_vi_tri"]
        constraints = [
            models.CheckConstraint(
                name="vitrikho_suc_chua_duong",
                condition=models.Q(suc_chua_toi_da__gt=0),
            ),
        ]

    def __str__(self):
        return f"{self.kho.ma_kho} - {self.ma_vi_tri}"


class TaiKhoanKeToan(models.Model):
    ma_tk = models.CharField(max_length=20, unique=True, verbose_name="Mã tài khoản")
    ten_tk = models.CharField(max_length=255, verbose_name="Tên tài khoản")
    tk_me = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tai_khoan_con',
        verbose_name="Tài khoản mẹ",
    )
    trang_thai = models.BooleanField(default=True, verbose_name="Trạng thái")

    class Meta:
        db_table = "danh_muc_taikhoanketoan"
        verbose_name = "Tài khoản kế toán"
        verbose_name_plural = "Danh mục tài khoản kế toán"
        ordering = ["ma_tk"]

    def __str__(self):
        return f"{self.ma_tk} - {self.ten_tk}"
