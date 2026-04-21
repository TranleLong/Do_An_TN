import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.ban_hang.models import HoaDonBan, PhieuThu
from apps.kho.models import PhieuNhap, PhieuXuat, KiemKe
from apps.so_cai.services import post_to_ledger, LedgerPostingError

def catch_up():
    print("Starting Ledger Catch-up...")
    
    # 1. Hoa Don Ban (status 2, 3)
    invoices = HoaDonBan.objects.filter(trang_thai__in=['2', '3'])
    print(f"Checking {invoices.count()} Invoices...")
    for inv in invoices:
        try:
            post_to_ledger('hoa_don_ban', inv.id)
            print(f"  [OK] Invoice {inv.so_hoa_don}")
        except LedgerPostingError as e:
            print(f"  [FAIL] Invoice {inv.so_hoa_don}: {str(e)}")

    # 2. Phieu Thu (status 2)
    receipts = PhieuThu.objects.filter(trang_thai='2')
    print(f"Checking {receipts.count()} Receipts...")
    for pt in receipts:
        try:
            post_to_ledger('phieu_thu', pt.id)
            print(f"  [OK] Receipt {pt.so_phieu}")
        except LedgerPostingError as e:
            print(f"  [FAIL] Receipt {pt.so_phieu}: {str(e)}")

    # 3. Phieu Nhap (status 3)
    pns = PhieuNhap.objects.filter(trang_thai='3')
    print(f"Checking {pns.count()} Goods Receipts...")
    for pn in pns:
        try:
            post_to_ledger('phieu_nhap', pn.id)
            print(f"  [OK] Goods Receipt {pn.so_phieu}")
        except LedgerPostingError as e:
            print(f"  [FAIL] Goods Receipt {pn.so_phieu}: {str(e)}")

    # 4. Phieu Xuat (status 3)
    pxs = PhieuXuat.objects.filter(trang_thai='3')
    print(f"Checking {pxs.count()} Goods Issues...")
    for px in pxs:
        try:
            post_to_ledger('phieu_xuat', px.id)
            print(f"  [OK] Goods Issue {px.so_phieu}")
        except LedgerPostingError as e:
            print(f"  [FAIL] Goods Issue {px.so_phieu}: {str(e)}")

    # 5. Kiem Ke (status 3)
    kks = KiemKe.objects.filter(trang_thai='3')
    print(f"Checking {kks.count()} Inventory Adjustments...")
    for kk in kks:
        try:
            post_to_ledger('phieu_dieu_chinh_kho', kk.id)
            print(f"  [OK] Audit {kk.id}")
        except LedgerPostingError as e:
            print(f"  [FAIL] Audit {kk.id}: {str(e)}")

    print("Catch-up complete.")

if __name__ == '__main__':
    catch_up()
