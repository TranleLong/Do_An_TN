import os
import django
from decimal import Decimal

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.danh_muc.models import Kho, TaiKhoanKeToan, ViTriKho

def init_danh_muc():
    print("=== [Init] Kho ===")
    if not Kho.objects.filter(ma_kho='KHO_CHINH').exists():
        Kho.objects.create(ma_kho='KHO_CHINH', ten_kho='Kho chính', dia_chi='Hà Nội')
        print("✓ Tạo Kho chính thành công")
    else:
        print("✓ Kho chính đã tồn tại")

    print("\n=== [Init] Hệ thống tài khoản kế toán ===")
    accounts = [
        ('1111', 'Tiền mặt'),
        ('1121', 'Tiền gửi ngân hàng (VND)'),
        ('131', 'Phải thu khách hàng'),
        ('156', 'Hàng hóa'),
        ('331', 'Phải trả người bán'),
        ('511', 'Doanh thu bán hàng'),
        ('632', 'Giá vốn hàng bán'),
        ('642', 'Chi phí quản lý doanh nghiệp'),
        ('911', 'Xác nhận kết quả kinh doanh'),
    ]
    
    count_tk = 0
    for ma, ten in accounts:
        if not TaiKhoanKeToan.objects.filter(ma_tk=ma).exists():
            TaiKhoanKeToan.objects.create(ma_tk=ma, ten_tk=ten)
            count_tk += 1
    
    print(f"✓ Đã thêm mới {count_tk} tài khoản kế toán")
    print("✓ Hệ thống tài khoản đã sẵn sàng")

def init_vi_tri_kho():
    print("\n=== [Init] Vị trí kho (từ CSDL local) ===")
    vitri_data = [
        {"ma": "A1-01", "mota": "Kệ A1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K01-T01", "mota": "Ben A - Day 1 - Ke 1 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K01-T02", "mota": "Ben A - Day 1 - Ke 1 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K01-T03", "mota": "Ben A - Day 1 - Ke 1 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K02-T01", "mota": "Ben A - Day 1 - Ke 2 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K02-T02", "mota": "Ben A - Day 1 - Ke 2 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K02-T03", "mota": "Ben A - Day 1 - Ke 2 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K03-T01", "mota": "Ben A - Day 1 - Ke 3 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K03-T02", "mota": "Ben A - Day 1 - Ke 3 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K03-T03", "mota": "Ben A - Day 1 - Ke 3 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K04-T01", "mota": "Ben A - Day 1 - Ke 4 - Tang 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K04-T02", "mota": "Ben A - Day 1 - Ke 4 - Tang 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K04-T03", "mota": "Ben A - Day 1 - Ke 4 - Tang 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K01-T02", "mota": "", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K01-T04", "mota": "Bên A - Dãy 1 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K01-T05", "mota": "Bên A - Dãy 1 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K02-T04", "mota": "Bên A - Dãy 1 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K02-T05", "mota": "Bên A - Dãy 1 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K03-T04", "mota": "Bên A - Dãy 1 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K03-T05", "mota": "Bên A - Dãy 1 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K04-T04", "mota": "Bên A - Dãy 1 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D01-K04-T05", "mota": "Bên A - Dãy 1 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K01-T01", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K01-T03", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K01-T04", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K01-T05", "mota": "Bên A - Dãy 2 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K02-T01", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K02-T02", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K02-T03", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K02-T04", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K02-T05", "mota": "Bên A - Dãy 2 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K03-T01", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K03-T02", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K03-T03", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K03-T04", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K03-T05", "mota": "Bên A - Dãy 2 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K04-T01", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K04-T02", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K04-T03", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K04-T04", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D02-K04-T05", "mota": "Bên A - Dãy 2 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K01-T01", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K01-T02", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K01-T03", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K01-T04", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K01-T05", "mota": "Bên A - Dãy 3 - Kệ 1 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K02-T01", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K02-T02", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K02-T03", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K02-T04", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K02-T05", "mota": "Bên A - Dãy 3 - Kệ 2 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K03-T01", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K03-T02", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K03-T03", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K03-T04", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K03-T05", "mota": "Bên A - Dãy 3 - Kệ 3 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K04-T01", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 1", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K04-T02", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 2", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K04-T03", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 3", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K04-T04", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 4", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "A-D03-K04-T05", "mota": "Bên A - Dãy 3 - Kệ 4 - Vị trí 5", "kho": "KHO_CHINH", "loai": "vua"},
        {"ma": "HL-KHO_CHINH-01", "mota": "Vị trí hàng lỗi", "kho": "KHO_CHINH", "loai": "nho"},
    ]

    kho_chinh = Kho.objects.filter(ma_kho='KHO_CHINH').first()
    if not kho_chinh:
        print("❌ Lỗi: Không tìm thấy Kho chính để gán vị trí")
        return

    count_vt = 0
    for v in vitri_data:
        if not ViTriKho.objects.filter(ma_vi_tri=v['ma'], kho=kho_chinh).exists():
            ViTriKho.objects.create(
                ma_vi_tri=v['ma'],
                mo_ta=v['mota'],
                kho=kho_chinh,
                loai_o=v['loai']
            )
            count_vt += 1
    
    print(f"✓ Đã thêm mới {count_vt} vị trí kho")

if __name__ == "__main__":
    try:
        init_danh_muc()
        init_vi_tri_kho()
        print("\n=== HOÀN TẤT KHỞI TẠO DỮ LIỆU DEMO ===")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
