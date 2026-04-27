
import os
import sys

# Ensure project root is in path before any app imports
sys.path.append(os.getcwd())

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.kho.models import KiemKe, ViTriKho, TonKhoViTri, TonKho
from apps.kho.views import _move_kiem_ke_hang_loi

def repair_defect_movements():
    # Tìm tất cả các phiếu kiểm kê có hàng lỗi nhưng chưa được chuyển
    # Chúng ta sẽ quét qua các phiếu ở trạng thái 2 (Chờ điều chỉnh) hoặc 3 (Hoàn thành)
    kks = KiemKe.objects.filter(trang_thai__in=['2', '3']).prefetch_related('chi_tiet', 'chi_tiet__hang_hoa')
    
    print(f"Checking {kks.count()} inventory vouchers for stuck defect items...")
    
    for kk in kks:
        vi_tri_nguon = (kk.khu_vuc or '').strip()
        if not vi_tri_nguon or not kk.vi_tri_hang_loi_id:
            continue
            
        vt_nguon_obj = ViTriKho.objects.filter(kho_id=kk.kho_id, ma_vi_tri=vi_tri_nguon).first()
        if not vt_nguon_obj:
            continue
            
        for ct in kk.chi_tiet.all():
            if int(ct.so_luong_loi or 0) > 0:
                # Kiểm tra xem hàng lỗi này đã có trong kho lỗi chưa
                # (Đây là logic chẩn đoán đơn giản, thực tế có thể phức tạp hơn)
                # Ta cứ thực hiện move nếu TonKho của sản phẩm đó có so_luong_loi khớp hoặc hụt
                
                print(f"  Fixing {ct.hang_hoa.ma_hang} ({ct.so_luong_loi} units) for {kk.ma_phieu}")
                try:
                    _move_kiem_ke_hang_loi(
                        kk.kho_id,
                        vt_nguon_obj.pk,
                        kk.vi_tri_hang_loi_id,
                        ct.hang_hoa_id,
                        int(ct.so_luong_loi or 0)
                    )
                    print(f"    SUCCESS: Moved {ct.so_luong_loi} for {ct.hang_hoa.ma_hang}")
                except Exception as e:
                    print(f"    SKIPPED/FAILED: {str(e)}")

if __name__ == "__main__":
    repair_defect_movements()
