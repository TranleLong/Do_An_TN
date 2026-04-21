import os
import django

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.danh_muc.models import Kho, TaiKhoanKeToan

def init_danh_muc():
    print("=== [Init] Kho ===")
    if not Kho.objects.filter(ma_kho='K01').exists():
        Kho.objects.create(ma_kho='K01', ten_kho='Kho chính', dia_chi='Hà Nội')
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
    
    count = 0
    for ma, ten in accounts:
        if not TaiKhoanKeToan.objects.filter(ma_tk=ma).exists():
            TaiKhoanKeToan.objects.create(ma_tk=ma, ten_tk=ten)
            count += 1
    
    print(f"✓ Đã thêm mới {count} tài khoản kế toán")
    print("✓ Hệ thống tài khoản đã sẵn sàng")

if __name__ == "__main__":
    try:
        init_danh_muc()
        print("\n=== HOÀN TẤT KHỞI TẠO DỮ LIỆU DEMO ===")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
