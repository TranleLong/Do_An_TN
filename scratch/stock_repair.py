from django.db.models import Sum
from django.utils import timezone
from apps.kho.models import TonKho, PhieuNhap_CT, PhieuXuat_CT, PhieuDieuChinhKiemKe_CT, TonKhoViTri

def run_repair():
    tks = TonKho.objects.all()
    count_fixed = 0
    for tk in tks:
        # 1. Tính tổng nhập (NK trạng thái Hoàn thành)
        nhap = PhieuNhap_CT.objects.filter(
            hang_hoa=tk.hang_hoa, 
            phieu_nhap__kho=tk.kho, 
            phieu_nhap__trang_thai='3'
        ).aggregate(s=Sum('so_luong_nhan'))['s'] or 0
        
        # 2. Tính tổng xuất (XK trạng thái Hoàn thành/Chưa hạch toán)
        xuat = PhieuXuat_CT.objects.filter(
            hang_hoa=tk.hang_hoa, 
            phieu_xuat__kho=tk.kho, 
            phieu_xuat__trang_thai__in=['2', '3']
        ).aggregate(s=Sum('so_luong'))['s'] or 0
        
        # 3. Tính tổng điều chỉnh (DC trạng thái Đã duyệt)
        dc = PhieuDieuChinhKiemKe_CT.objects.filter(
            hang_hoa=tk.hang_hoa,
            phieu__kho=tk.kho,
            phieu__trang_thai='2'
        ).aggregate(s=Sum('chenh_lech'))['s'] or 0
        
        real_total = nhap - xuat + dc
        
        if tk.so_luong != real_total:
            print(f"Repairing {tk.hang_hoa.ma_hang}: {tk.so_luong} -> {real_total}")
            tk.so_luong = real_total
            if real_total <= 0:
                tk.so_luong_loi = 0
                tk.so_luong = 0
            tk.ngay_cap_nhat = timezone.now()
            tk.save()
            count_fixed += 1
            
        # Nếu tồn bằng 0, xóa sạch phân bổ vị trí
        if tk.so_luong <= 0:
            TonKhoViTri.objects.filter(kho=tk.kho, hang_hoa=tk.hang_hoa).delete()

    print(f"Finished repairing {count_fixed} records.")

if __name__ == "__main__":
    run_repair()
