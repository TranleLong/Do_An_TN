from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.danh_muc.models import KhachHang, Kho, NhaCungCap, TaiKhoanKeToan


class JournalEntry(models.Model):
    DOC_TYPE_CHOICES = [
        ('hoa_don_ban', 'Hoa don ban hang'),
        ('phieu_thu', 'Phieu thu'),
        ('phieu_nhap', 'Phieu nhap kho'),
        ('phieu_xuat', 'Phieu xuat kho'),
        ('phieu_dieu_chinh_kho', 'Phieu dieu chinh kho'),
        ('hang_ban_tra_lai', 'Hang ban bi tra lai'),
        ('dao_but_toan', 'Dao but toan'),
    ]

    STATUS_CHOICES = [
        ('posted', 'Da ghi so'),
        ('reversed', 'Da dao'),
    ]

    entry_number = models.CharField(max_length=30, unique=True, verbose_name='So chung tu ghi so')
    document_type = models.CharField(max_length=40, choices=DOC_TYPE_CHOICES, verbose_name='Loai chung tu')
    document_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID chung tu nguon')
    document_number = models.CharField(max_length=50, blank=True, verbose_name='So chung tu nguon')
    document_date = models.DateField(verbose_name='Ngay chung tu')
    posting_date = models.DateField(verbose_name='Ngay ghi so')
    description = models.TextField(blank=True, verbose_name='Dien giai')

    customer = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Khach hang')
    supplier = models.ForeignKey(NhaCungCap, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nha cung cap')
    warehouse = models.ForeignKey(Kho, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Kho')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='posted', verbose_name='Trang thai')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nguoi ghi so')
    reversed_entry = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reverse_of',
        verbose_name='Chung tu dao',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'so_cai_journal_entry'
        verbose_name = 'Chung tu ghi so'
        verbose_name_plural = 'Chung tu ghi so'
        ordering = ['-posting_date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'document_id'],
                condition=models.Q(status='posted') & ~models.Q(document_type='dao_but_toan'),
                name='uniq_so_cai_posted_per_document',
            )
        ]
        indexes = [
            models.Index(fields=['document_type', 'document_id']),
            models.Index(fields=['posting_date']),
            models.Index(fields=['document_number']),
        ]

    def __str__(self):
        return self.entry_number

    @property
    def total_debit(self):
        return self.lines.aggregate(v=Sum('debit_amount'))['v'] or Decimal('0')

    @property
    def total_credit(self):
        return self.lines.aggregate(v=Sum('credit_amount'))['v'] or Decimal('0')

    def clean(self):
        if self.posting_date < self.document_date:
            raise ValidationError('Ngay ghi so khong duoc nho hon ngay chung tu.')


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    line_no = models.PositiveIntegerField(default=1, verbose_name='So dong')
    account = models.ForeignKey(TaiKhoanKeToan, on_delete=models.PROTECT, verbose_name='Tai khoan')
    debit_amount = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Phat sinh no')
    credit_amount = models.DecimalField(max_digits=18, decimal_places=0, default=0, verbose_name='Phat sinh co')

    customer = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(NhaCungCap, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Kho, on_delete=models.SET_NULL, null=True, blank=True)

    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'so_cai_journal_entry_line'
        verbose_name = 'Dong but toan'
        verbose_name_plural = 'Dong but toan'
        ordering = ['journal_entry_id', 'line_no', 'id']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['journal_entry', 'line_no']),
        ]

    def clean(self):
        debit = Decimal(self.debit_amount or 0)
        credit = Decimal(self.credit_amount or 0)
        if debit < 0 or credit < 0:
            raise ValidationError('So tien no/co khong duoc am.')
        if debit == 0 and credit == 0:
            raise ValidationError('Dong but toan phai co No hoac Co.')
        if debit > 0 and credit > 0:
            raise ValidationError('Mot dong but toan khong duoc co dong thoi No va Co.')

    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.account.ma_tk}"
