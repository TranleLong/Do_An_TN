"""Views cho app Core: Dashboard, HangHoa, Kho"""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import DonViTinh, HangHoa, Kho, NhomHang, ThuongHieu


@login_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    from apps.ban_hang.models import DonBan
    from apps.danh_muc.models import KhachHang, NhaCungCap

    try:
        # KPI
        tong_hang_hoa = HangHoa.objects.filter(trang_thai='dang_ban').count()
        tong_kh = KhachHang.objects.filter(trang_thai=True).count()
        tong_ncc = NhaCungCap.objects.filter(trang_thai=True).count()

        doanh_thu_thang = DonBan.objects.filter(
            trang_thai='da_xac_nhan', ngay_ban__gte=month_start
        ).aggregate(total=Sum('tong_thanh_toan'))['total'] or 0

        don_ban_hom_nay = DonBan.objects.filter(ngay_ban=today).count()

        # Hàng sắp hết kho
        hang_sap_het = []
        for h in HangHoa.objects.filter(trang_thai='dang_ban'):
            ton = h.get_ton_kho()
            if ton <= h.ton_toi_thieu:
                hang_sap_het.append({'hang': h, 'ton': ton})
        hang_sap_het = hang_sap_het[:8]

        # Đơn bán gần đây
        don_ban_gan_day = DonBan.objects.select_related('khach_hang').order_by('-ngay_tao')[:8]

        # Doanh thu 7 ngày gần đây (cho biểu đồ)
        chart_labels = []
        chart_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            label = d.strftime('%d/%m')
            dt = DonBan.objects.filter(
                trang_thai='da_xac_nhan', ngay_ban=d
            ).aggregate(t=Sum('tong_thanh_toan'))['t'] or 0
            chart_labels.append(f"'{label}'")
            chart_data.append(float(dt))
    except (OperationalError, ProgrammingError):
        messages.warning(
            request,
            'Cơ sở dữ liệu nghiệp vụ chưa được khởi tạo. Bạn vẫn đăng nhập được, '
            'hãy chạy migrate khi cần sử dụng các màn hình nghiệp vụ.'
        )
        tong_hang_hoa = 0
        tong_kh = 0
        tong_ncc = 0
        doanh_thu_thang = 0
        don_ban_hom_nay = 0
        hang_sap_het = []
        don_ban_gan_day = []
        chart_labels = [
            f"'{(today - timedelta(days=i)).strftime('%d/%m')}'"
            for i in range(6, -1, -1)
        ]
        chart_data = [0, 0, 0, 0, 0, 0, 0]

    context = {
        'tong_hang_hoa': tong_hang_hoa,
        'tong_kh': tong_kh,
        'tong_ncc': tong_ncc,
        'doanh_thu_thang': doanh_thu_thang,
        'don_ban_hom_nay': don_ban_hom_nay,
        'hang_sap_het': hang_sap_het,
        'don_ban_gan_day': don_ban_gan_day,
        'chart_labels': ','.join(chart_labels),
        'chart_data': ','.join(str(x) for x in chart_data),
        'page_title': 'Dashboard',
        'active_menu': 'dashboard',
    }
    return render(request, 'dashboard.html', context)


# ─── HÀNG HÓA ─────────────────────────────────────────────────
@login_required
def hang_hoa_list(request):
    q = request.GET.get('q', '')
    nhom = request.GET.get('nhom', '')
    items = HangHoa.objects.select_related('nhom_hang', 'thuong_hieu', 'don_vi_tinh')
    if q:
        items = items.filter(Q(ma_hang__icontains=q) | Q(ten_hang__icontains=q) |
                             Q(xe_tuong_thich__icontains=q))
    if nhom:
        items = items.filter(nhom_hang_id=nhom)

    # Gắn tồn kho
    from apps.kho.models import TonKho
    hang_list = []
    for h in items:
        ton = TonKho.objects.filter(hang_hoa=h).aggregate(t=Sum('so_luong'))['t'] or 0
        hang_list.append({'hang': h, 'ton': ton})

    context = {
        'hang_list': hang_list,
        'nhom_list': NhomHang.objects.all(),
        'q': q,
        'nhom_filter': nhom,
        'page_title': 'Danh mục hàng hóa',
        'active_menu': 'hang_hoa',
    }
    return render(request, 'core/hang_hoa_list.html', context)


@login_required
def hang_hoa_form(request, pk=None):
    hang = get_object_or_404(HangHoa, pk=pk) if pk else None
    nhom_list = NhomHang.objects.all()
    thuong_hieu_list = ThuongHieu.objects.all()
    dvt_list = DonViTinh.objects.all()

    if request.method == 'POST':
        data = request.POST
        if not hang:
            hang = HangHoa()
        hang.ma_hang = data.get('ma_hang', '').strip()
        hang.ten_hang = data.get('ten_hang', '').strip()
        hang.nhom_hang_id = data.get('nhom_hang') or None
        hang.thuong_hieu_id = data.get('thuong_hieu') or None
        hang.don_vi_tinh_id = data.get('don_vi_tinh') or None
        hang.xe_tuong_thich = data.get('xe_tuong_thich', '')
        hang.barcode = data.get('barcode', '')
        hang.gia_ban_le = data.get('gia_ban_le', 0) or 0
        hang.gia_ban_buon = data.get('gia_ban_buon', 0) or 0
        hang.ton_toi_thieu = data.get('ton_toi_thieu', 0) or 0
        hang.ton_toi_da = data.get('ton_toi_da', 0) or 0
        hang.trang_thai = data.get('trang_thai', 'dang_ban')
        hang.ghi_chu = data.get('ghi_chu', '')
        try:
            hang.save()
            messages.success(request, f'Đã lưu hàng hóa: {hang.ten_hang}')
            return redirect('hang_hoa_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')

    context = {
        'hang': hang,
        'nhom_list': nhom_list,
        'thuong_hieu_list': thuong_hieu_list,
        'dvt_list': dvt_list,
        'page_title': 'Thêm hàng hóa' if not pk else 'Sửa hàng hóa',
        'active_menu': 'hang_hoa',
    }
    return render(request, 'core/hang_hoa_form.html', context)


@login_required
def hang_hoa_xoa(request, pk):
    hang = get_object_or_404(HangHoa, pk=pk)
    if request.method == 'POST':
        hang.trang_thai = 'ngung_ban'
        hang.save()
        messages.success(request, f'Đã ngừng bán: {hang.ten_hang}')
    return redirect('hang_hoa_list')


@login_required
def hang_hoa_api(request):
    """API trả về thông tin hàng hóa theo mã - dùng cho form JS"""
    ma = request.GET.get('ma', '')
    from apps.kho.models import TonKho
    try:
        h = HangHoa.objects.get(ma_hang=ma)
        kho_id = request.GET.get('kho_id')
        ton = 0
        gia_von = 0
        if kho_id:
            tk = TonKho.objects.filter(hang_hoa=h, kho_id=kho_id).first()
            if tk:
                ton = tk.so_luong
                gia_von = float(tk.gia_von_tb)
        return JsonResponse({
            'id': h.id, 'ma_hang': h.ma_hang, 'ten_hang': h.ten_hang,
            'dvt': h.don_vi_tinh.ten if h.don_vi_tinh else '',
            'gia_ban_le': float(h.gia_ban_le),
            'gia_ban_buon': float(h.gia_ban_buon),
            'ton_kho': ton, 'gia_von': gia_von,
        })
    except HangHoa.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy'}, status=404)


# ─── KHO ────────────────────────────────────────────────────
@login_required
def kho_list(request):
    kho_list = Kho.objects.filter(trang_thai=True)
    context = {
        'kho_list': kho_list,
        'page_title': 'Danh sách kho',
        'active_menu': 'kho',
    }
    return render(request, 'core/kho_list.html', context)


# ─── Danh mục phụ ────────────────────────────────────────────
@login_required
def nhom_hang_list(request):
    items = NhomHang.objects.all()
    if request.method == 'POST':
        ma = request.POST.get('ma_nhom', '').strip()
        ten = request.POST.get('ten_nhom', '').strip()
        if ma and ten:
            NhomHang.objects.create(ma_nhom=ma, ten_nhom=ten)
            messages.success(request, 'Đã thêm nhóm hàng')
    return render(request, 'core/nhom_hang.html', {
        'items': items, 'page_title': 'Nhóm hàng', 'active_menu': 'danh_muc'
    })
