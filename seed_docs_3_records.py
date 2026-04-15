from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User

from apps.ban_hang.models import (DonBan, DonBan_CT, HoaDonBan, HoaDonBan_CT,
                                  PhieuGiaBan, PhieuGiaBan_CT, PhieuThu,
                                  PhieuTraHang, PhieuTraHang_CT)
from apps.danh_muc.models import HangHoa, KhachHang, Kho, NhomHang
from apps.kho.models import (PhieuNhap, PhieuNhap_CT, PhieuXuat, PhieuXuat_CT,
                             TonKho)


def _ensure_user():
    user = User.objects.first()
    if user:
        return user
    return User.objects.create_user(username="seed_user", password="123456", is_staff=True)


def _ensure_kho():
    kho, _ = Kho.objects.get_or_create(
        ma_kho="KHOSEED",
        defaults={"ten_kho": "Kho Seed", "trang_thai": True},
    )
    return kho


def _ensure_nhom_hang():
    nhoms = []
    for i in range(1, 4):
        ma = f"NHSEED{i:03d}"
        nhom, _ = NhomHang.objects.get_or_create(
            ma_nhom=ma,
            defaults={"ten_nhom": f"Nhóm seed {i}", "bien_do_loi_nhuan": Decimal("10")},
        )
        nhoms.append(nhom)
    return nhoms


def _ensure_khach_hang():
    khs = []
    for i in range(1, 4):
        ma = f"KHSEED{i:03d}"
        kh, _ = KhachHang.objects.get_or_create(
            ma_kh=ma,
            defaults={
                "ten_kh": f"Khách seed {i}",
                "so_dien_thoai": f"0900000{i:03d}",
                "la_khach_hang": True,
                "loai_kh": "1",
                "trang_thai": True,
            },
        )
        khs.append(kh)
    return khs


def _ensure_hang_hoa(nhoms):
    hangs = []
    for i in range(1, 4):
        ma = f"HHSEED{i:03d}"
        hang, _ = HangHoa.objects.get_or_create(
            ma_hang=ma,
            defaults={
                "ten_hang": f"Hàng seed {i}",
                "nhom_hang": nhoms[(i - 1) % len(nhoms)],
                "trang_thai": "dang_ban",
            },
        )
        if not hang.nhom_hang_id:
            hang.nhom_hang = nhoms[(i - 1) % len(nhoms)]
            hang.save(update_fields=["nhom_hang"])
        hangs.append(hang)
    return hangs


def _ensure_ton(hangs, kho):
    for i, h in enumerate(hangs, start=1):
        ton, _ = TonKho.objects.get_or_create(
            hang_hoa=h,
            kho=kho,
            defaults={"so_luong": 100 + i * 10, "gia_von_tb": Decimal("50000") + i * 1000},
        )
        if ton.so_luong < 20:
            ton.so_luong = 100 + i * 10
            ton.save(update_fields=["so_luong", "ngay_cap_nhat"])


def _seed_don_hang(user, kho, khs, hangs):
    created = 0
    for i in range(1, 4):
        so = f"DBSEED{i:03d}"
        don, was_created = DonBan.objects.get_or_create(
            so_don=so,
            defaults={
                "ngay_chung_tu": date.today(),
                "ngay_ban": date.today(),
                "loai_ban": "ban_le",
                "khach_hang": khs[(i - 1) % 3],
                "ten_kh": khs[(i - 1) % 3].ten_kh,
                "sdt_kh": khs[(i - 1) % 3].so_dien_thoai,
                "kho": kho,
                "nhan_vien_ban": user,
                "ma_nv_ban_hang": "NVSEED",
                "phuong_thuc_tt": "tien_mat",
                "trang_thai": "1",
            },
        )
        if was_created:
            DonBan_CT.objects.create(
                don_ban=don,
                hang_hoa=hangs[(i - 1) % 3],
                so_luong=2 + i,
                don_gia=Decimal("120000") + i * 5000,
                chiet_khau=Decimal("3"),
                thue_vat=Decimal("10"),
            )
            don.tinh_tong()
            created += 1
    return created


def _seed_hoa_don(user, kho, khs, hangs):
    created = 0
    for i in range(1, 4):
        so = f"HDSEED{i:03d}"
        kh = khs[(i - 1) % 3]
        don = DonBan.objects.filter(so_don=f"DBSEED{i:03d}").first()
        hd, was_created = HoaDonBan.objects.get_or_create(
            so_hoa_don=so,
            defaults={
                "ma_giao_dich": "1",
                "ngay_lap": date.today(),
                "ngay_hach_toan": date.today(),
                "khach_hang": kh,
                "ten_kh": kh.ten_kh,
                "so_dien_thoai": kh.so_dien_thoai,
                "ma_nv_ban_hang": "NVSEED",
                "tk_no": "131",
                "tk_co": "511",
                "trang_thai": "1",
                "don_ban": don,
                "nguoi_tao": user,
            },
        )
        if was_created:
            HoaDonBan_CT.objects.create(
                hoa_don=hd,
                hang_hoa=hangs[(i - 1) % 3],
                kho=kho,
                so_luong=2 + i,
                gia_ban=Decimal("150000") + i * 5000,
                ty_le_chiet_khau=Decimal("2"),
                thue_suat=Decimal("10"),
                tk_gia_von="632",
                tk_doanh_thu="511",
            )
            hd.tinh_tong()
            created += 1
    return created


def _seed_nhap_kho(user, kho, hangs):
    created = 0
    for i in range(1, 4):
        so = f"PNSEED{i:03d}"
        pn, was_created = PhieuNhap.objects.get_or_create(
            so_phieu=so,
            defaults={
                "ngay_lap": date.today(),
                "ngay_hach_toan": date.today(),
                "ngay_chung_tu": date.today(),
                "ngay_nhap": date.today(),
                "loai_nhap": "1",
                "kho": kho,
                "trang_thai": "1",
                "nguoi_tao": user,
                "ghi_chu": "[SEED] Phiếu nhập mẫu",
            },
        )
        if was_created:
            PhieuNhap_CT.objects.create(
                phieu_nhap=pn,
                hang_hoa=hangs[(i - 1) % 3],
                so_luong_dat=10 + i,
                so_luong_nhan=10 + i,
                don_gia=Decimal("80000") + i * 2000,
                chiet_khau=Decimal("0"),
                tk_no="156",
                tk_co="331",
            )
            pn.tinh_tong()
            created += 1
    return created


def _seed_xuat_kho(user, kho, hangs):
    created = 0
    for i in range(1, 4):
        so = f"PXSEED{i:03d}"
        px, was_created = PhieuXuat.objects.get_or_create(
            so_phieu=so,
            defaults={
                "ngay_lap": date.today(),
                "ngay_hach_toan": date.today(),
                "ngay_chung_tu": date.today(),
                "ngay_xuat": date.today(),
                "loai_xuat": "ban_hang",
                "kho": kho,
                "trang_thai": "1",
                "nguoi_tao": user,
                "ghi_chu": "[SEED] Phiếu xuất mẫu",
            },
        )
        if was_created:
            gia_von = Decimal("70000") + i * 1000
            so_luong = 2 + i
            PhieuXuat_CT.objects.create(
                phieu_xuat=px,
                hang_hoa=hangs[(i - 1) % 3],
                so_luong=so_luong,
                gia_von=gia_von,
                tong_gia_von=gia_von * so_luong,
                tk_no="632",
                tk_co="156",
            )
            px.tong_gia_von = gia_von * so_luong
            px.save(update_fields=["tong_gia_von"])
            created += 1
    return created


def _seed_doi_tra(user, kho, khs, hangs):
    created = 0
    for i in range(1, 4):
        so = f"DTSEED{i:03d}"
        kh = khs[(i - 1) % 3]
        hd = HoaDonBan.objects.filter(so_hoa_don=f"HDSEED{i:03d}").first()
        don = DonBan.objects.filter(so_don=f"DBSEED{i:03d}").first()
        pt, was_created = PhieuTraHang.objects.get_or_create(
            so_phieu=so,
            defaults={
                "ngay_lap": date.today(),
                "ngay_hach_toan": date.today(),
                "ngay_tra": date.today(),
                "hoa_don_goc": hd,
                "don_ban_goc": don,
                "khach_hang": kh,
                "tk_no": "531",
                "tk_co": "131",
                "hinh_thuc_xu_ly": "tra_hang",
                "ly_do_tra": "[SEED] Trả hàng mẫu",
                "hinh_thuc_hoan": "2",
                "trang_thai": "1",
                "nguoi_tao": user,
            },
        )
        if was_created:
            PhieuTraHang_CT.objects.create(
                phieu_tra=pt,
                kho=kho,
                hang_hoa=hangs[(i - 1) % 3],
                so_luong=1,
                don_gia=Decimal("120000") + i * 3000,
                loai_hang_tra="binh_thuong",
            )
            created += 1
    return created


def _seed_gia_ban(user, nhoms, hangs):
    created = 0
    for i in range(1, 4):
        ma = f"GBSEED{i:03d}"
        nhom = nhoms[(i - 1) % 3]
        phieu, was_created = PhieuGiaBan.objects.get_or_create(
            ma_phieu=ma,
            defaults={
                "ngay_lap": date.today(),
                "ngay_hieu_luc": date.today(),
                "nguoi_lap": user,
                "nhom_hang": nhom,
                "bien_do_loi_nhuan": Decimal("12"),
                "loai_tien_te": "VND",
                "trang_thai_duyet": "1",
                "ghi_chu": "[SEED] Phiếu giá bán mẫu",
            },
        )
        if was_created:
            hang = hangs[(i - 1) % 3]
            PhieuGiaBan_CT.objects.create(
                phieu=phieu,
                hang_hoa=hang,
                gia_von=Decimal("90000") + i * 2000,
                gia_ban_chuan=Decimal("120000") + i * 3000,
            )
            created += 1
    return created


def _seed_thu_chi(user, khs):
    created_thu = 0
    created_chi = 0

    for i in range(1, 4):
        pt, was_created = PhieuThu.objects.get_or_create(
            so_phieu=f"PTSEED{i:03d}",
            defaults={
                "ngay_thu": date.today(),
                "khach_hang": khs[(i - 1) % 3],
                "hinh_thuc_thu": "tien_mat",
                "tong_thu": Decimal("200000") + i * 10000,
                "trang_thai": "1",
                "nguoi_tao": user,
                "ghi_chu": "[SEED] Phiếu thu mẫu",
            },
        )
        if was_created:
            created_thu += 1

        pc, was_created = PhieuThu.objects.get_or_create(
            so_phieu=f"PCSEED{i:03d}",
            defaults={
                "ngay_thu": date.today(),
                "khach_hang": khs[(i - 1) % 3],
                "hinh_thuc_thu": "chuyen_khoan",
                "tong_thu": Decimal("150000") + i * 8000,
                "trang_thai": "1",
                "nguoi_tao": user,
                "ghi_chu": "[LOAI_PHIEU:CHI] [SEED] Phiếu chi mẫu",
            },
        )
        if was_created:
            created_chi += 1

    return created_thu, created_chi


def run():
    user = _ensure_user()
    kho = _ensure_kho()
    nhoms = _ensure_nhom_hang()
    khs = _ensure_khach_hang()
    hangs = _ensure_hang_hoa(nhoms)
    _ensure_ton(hangs, kho)

    c_don = _seed_don_hang(user, kho, khs, hangs)
    c_hd = _seed_hoa_don(user, kho, khs, hangs)
    c_nhap = _seed_nhap_kho(user, kho, hangs)
    c_xuat = _seed_xuat_kho(user, kho, hangs)
    c_doi_tra = _seed_doi_tra(user, kho, khs, hangs)
    c_gia = _seed_gia_ban(user, nhoms, hangs)
    c_thu, c_chi = _seed_thu_chi(user, khs)

    print("=== SEED KET QUA ===")
    print(f"Don ban tao moi: {c_don}")
    print(f"Hoa don tao moi: {c_hd}")
    print(f"Phieu nhap tao moi: {c_nhap}")
    print(f"Phieu xuat tao moi: {c_xuat}")
    print(f"Phieu doi tra tao moi: {c_doi_tra}")
    print(f"Phieu gia ban tao moi: {c_gia}")
    print(f"Phieu thu tao moi: {c_thu}")
    print(f"Phieu chi tao moi: {c_chi}")


run()
