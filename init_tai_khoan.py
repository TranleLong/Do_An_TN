"""Script khởi tạo dữ liệu tài khoản kế toán cho hệ thống."""

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.danh_muc.models import TaiKhoanKeToan

# Xóa dữ liệu cũ (optional, bỏ dòng này nếu muốn giữ)
# TaiKhoanKeToan.objects.all().delete()

# Dữ liệu tài khoản kế toán (chuẩn mã >= 3 số)
taikhoan_data = [
    # Tiền và công nợ
    ('111', 'Tiền mặt', None, True),
    ('112', 'Tiền gửi ngân hàng', None, True),
    ('131', 'Phải thu khách hàng', None, True),
    ('1331', 'Thuế GTGT được khấu trừ của hàng hóa, dịch vụ', None, True),
    ('1388', 'Phải thu khác', None, True),
    ('141', 'Tạm ứng', None, True),

    # Kho và hàng hóa
    ('152', 'Nguyên liệu, vật liệu', None, True),
    ('153', 'Công cụ, dụng cụ', None, True),
    ('155', 'Thành phẩm', None, True),
    ('156', 'Hàng hóa', None, True),
    ('157', 'Hàng gửi đi bán', None, True),

    # Tài sản cố định
    ('211', 'Tài sản cố định hữu hình', None, True),
    ('214', 'Hao mòn tài sản cố định', None, True),
    ('242', 'Chi phí trả trước', None, True),

    # Nợ phải trả
    ('311', 'Vay ngắn hạn', None, True),
    ('331', 'Phải trả cho người bán', None, True),
    ('3331', 'Thuế GTGT phải nộp', None, True),
    ('3334', 'Thuế thu nhập doanh nghiệp', None, True),
    ('334', 'Phải trả người lao động', None, True),
    ('338', 'Phải trả, phải nộp khác', None, True),
    ('341', 'Vay và nợ thuê tài chính', None, True),

    # Vốn chủ sở hữu
    ('411', 'Vốn đầu tư của chủ sở hữu', None, True),
    ('421', 'Lợi nhuận sau thuế chưa phân phối', None, True),

    # Doanh thu
    ('511', 'Doanh thu bán hàng và cung cấp dịch vụ', None, True),
    ('515', 'Doanh thu hoạt động tài chính', None, True),
    ('521', 'Các khoản giảm trừ doanh thu', None, True),
    ('531', 'Hàng bán bị trả lại', None, True),

    # Giá vốn và chi phí
    ('632', 'Giá vốn hàng bán', None, True),
    ('635', 'Chi phí tài chính', None, True),
    ('641', 'Chi phí bán hàng', None, True),
    ('642', 'Chi phí quản lý doanh nghiệp', None, True),

    # Thu nhập/chi phí khác và xác định kết quả
    ('711', 'Thu nhập khác', None, True),
    ('811', 'Chi phí khác', None, True),
    ('911', 'Xác định kết quả kinh doanh', None, True),
]

created = 0
updated = 0
skipped = 0

# Dọn các mã cũ không hợp lệ (<3 ký tự)
for tk in TaiKhoanKeToan.objects.all():
    if len((tk.ma_tk or '').strip()) < 3:
        tk.delete()

for ma_tk, ten_tk, tk_me_ma, trang_thai in taikhoan_data:
    # Tìm tài khoản cha (nếu có)
    tk_me = None
    if tk_me_ma:
        try:
            tk_me = TaiKhoanKeToan.objects.get(ma_tk=tk_me_ma)
        except TaiKhoanKeToan.DoesNotExist:
            print(f"⚠️  Cảnh báo: Tài khoản cha '{tk_me_ma}' không tìm thấy cho '{ma_tk}'")
    
    # Kiểm tra xem đã tồn tại chưa
    obj, is_created = TaiKhoanKeToan.objects.get_or_create(
        ma_tk=ma_tk,
        defaults={
            'ten_tk': ten_tk,
            'tk_me': tk_me,
            'trang_thai': trang_thai,
        }
    )
    
    if is_created:
        print(f"✓ Tạo mới: {ma_tk:8} - {ten_tk}")
        created += 1
    else:
        # Cập nhật nếu dữ liệu thay đổi
        needs_update = False
        if obj.ten_tk != ten_tk:
            obj.ten_tk = ten_tk
            needs_update = True
        if obj.tk_me != tk_me:
            obj.tk_me = tk_me
            needs_update = True
        if obj.trang_thai != trang_thai:
            obj.trang_thai = trang_thai
            needs_update = True
        
        if needs_update:
            obj.save()
            print(f"↻ Cập nhật: {ma_tk:8} - {ten_tk}")
            updated += 1
        else:
            skipped += 1

print(f"\n{'='*60}")
print(f"Kết quả khởi tạo dữ liệu tài khoản kế toán:")
print(f"  • Tạo mới: {created} tài khoản")
print(f"  • Cập nhật: {updated} tài khoản")
print(f"  • Bỏ qua: {skipped} tài khoản (đã tồn tại)")
print(f"  • Tổng cộng: {TaiKhoanKeToan.objects.count()} tài khoản trong hệ thống")
print(f"{'='*60}")
print("✓ Khởi tạo dữ liệu thành công!")
