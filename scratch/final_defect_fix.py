import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.kho.models import KiemKe, TonKhoViTri
from apps.kho.views import _move_kiem_ke_hang_loi, _find_kiem_ke_vi_tri, _resync_tonkho_from_vitri_scope
from django.db import transaction

def global_repair():
    pkk_list = KiemKe.objects.filter(trang_thai__in=['2', '3'])
    print(f"Scanning {len(pkk_list)} vouchers for missed defect movements...")
    
    for kk in pkk_list:
        src_vt = _find_kiem_ke_vi_tri(kk)
        dest_vt = kk.vi_tri_hang_loi
        if not src_vt or not dest_vt:
            continue
            
        with transaction.atomic():
            for ct in kk.chi_tiet.filter(so_luong_loi__gt=0):
                # Kiểm tra xem hàng đã được chuyển vào kho lỗi chưa?
                d_row = TonKhoViTri.objects.filter(kho=kk.kho, vi_tri=dest_vt, hang_hoa=ct.hang_hoa).first()
                cur_d = int(d_row.so_luong if d_row else 0)
                
                required = int(ct.so_luong_loi)
                if cur_d < required:
                    to_move = required - cur_d
                    print(f"  [Fixing {kk.ma_phieu}] Moving {to_move} units of {ct.hang_hoa.ma_hang} from {src_vt.ma_vi_tri} to {dest_vt.ma_vi_tri}")
                    _move_kiem_ke_hang_loi(kk.kho_id, src_vt.pk, dest_vt.pk, ct.hang_hoa_id, to_move)
    
    # Đồng bộ lại toàn bộ kho để Header khớp 100%
    _resync_tonkho_from_vitri_scope(kho_id=1)

if __name__ == "__main__":
    global_repair()
    print("GLOBAL SCAN & FIX COMPLETED")
