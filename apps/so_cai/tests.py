from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.ban_hang.models import HoaDonBan, HoaDonBan_CT, PhieuThu
from apps.danh_muc.models import (DonViTinh, HangHoa, KhachHang, Kho, NhomHang,
                                  TaiKhoanKeToan)

from .models import JournalEntry
from .services import get_general_ledger, get_trial_balance, post_to_ledger


class LedgerServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='123456')
        self.kho = Kho.objects.create(ma_kho='K1', ten_kho='Kho Tong')
        self.khach = KhachHang.objects.create(ma_kh='KH001', ten_kh='Khach 1', so_dien_thoai='0900000000')
        self.nhom = NhomHang.objects.create(ma_nhom='NH1', ten_nhom='Nhom')
        self.dvt = DonViTinh.objects.create(ten='Cai')
        self.hang = HangHoa.objects.create(ma_hang='H001', ten_hang='Hang 1', nhom_hang=self.nhom, don_vi_tinh=self.dvt)

        for code, name in [
            ('111', 'Tien mat'),
            ('112', 'Tien gui NH'),
            ('131', 'Phai thu KH'),
            ('156', 'Hang hoa'),
            ('331', 'Phai tra NCC'),
            ('511', 'Doanh thu BH'),
            ('632', 'Gia von'),
            ('3331', 'Thue GTGT dau ra'),
        ]:
            TaiKhoanKeToan.objects.create(ma_tk=code, ten_tk=name)

    def test_post_invoice_to_ledger_only_once(self):
        hd = HoaDonBan.objects.create(
            so_hoa_don='HD001',
            khach_hang=self.khach,
            ten_kh=self.khach.ten_kh,
            tk_no='131',
            trang_thai='3',
        )
        HoaDonBan_CT.objects.create(
            hoa_don=hd,
            hang_hoa=self.hang,
            kho=self.kho,
            so_luong=Decimal('1'),
            gia_ban=Decimal('1000000'),
            ty_le_chiet_khau=Decimal('0'),
            thue_suat=Decimal('10'),
            tk_doanh_thu='511',
            tk_gia_von='632',
        )
        hd.tinh_tong()

        entry_1 = post_to_ledger('hoa_don_ban', hd.id, user=self.user)
        entry_2 = post_to_ledger('hoa_don_ban', hd.id, user=self.user)

        self.assertEqual(entry_1.id, entry_2.id)
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(entry_1.total_debit, entry_1.total_credit)

    def test_post_receipt_and_query_ledger(self):
        pt = PhieuThu.objects.create(
            so_phieu='PT001',
            khach_hang=self.khach,
            hinh_thuc_thu='tien_mat',
            tong_thu=Decimal('500000'),
            trang_thai='3',
            nguoi_tao=self.user,
        )

        post_to_ledger('phieu_thu', pt.id, user=self.user)

        report = get_general_ledger('111', pt.ngay_thu, pt.ngay_thu)
        self.assertEqual(report['total_debit'], Decimal('500000'))
        self.assertEqual(report['total_credit'], Decimal('0'))

        trial = get_trial_balance(pt.ngay_thu, pt.ngay_thu)
        self.assertTrue(trial['total_period_debit'] > 0)
        self.assertEqual(trial['total_period_debit'], trial['total_period_credit'])
