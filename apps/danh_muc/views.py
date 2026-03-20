"""Views cho app Danh Mục: KhachHang, NhaCungCap"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import KhachHang, NhaCungCap, NhomKhachHang


# ─── KHÁCH HÀNG ──────────────────────────────────────────────
@login_required
def kh_list(request):
    q = request.GET.get('q', '')
    items = KhachHang.objects.filter(trang_thai=True)
    if q:
        items = items.filter(Q(ma_kh__icontains=q) | Q(ten_kh__icontains=q) |
                             Q(so_dien_thoai__icontains=q))
    return render(request, 'danh_muc/kh_list.html', {
        'items': items, 'q': q,
        'page_title': 'Danh sách khách hàng', 'active_menu': 'khach_hang',
    })


@login_required
def kh_form(request, pk=None):
    obj = get_object_or_404(KhachHang, pk=pk) if pk else None
    if request.method == 'POST':
        data = request.POST
        if not obj:
            obj = KhachHang()
        obj.ma_kh = data.get('ma_kh', '').strip()
        obj.ten_kh = data.get('ten_kh', '').strip()
        obj.loai_kh = data.get('loai_kh', 'ca_nhan')
        obj.nhom_kh_id = data.get('nhom_kh') or None
        obj.ma_so_thue = data.get('ma_so_thue', '')
        obj.dia_chi = data.get('dia_chi', '')
        obj.so_dien_thoai = data.get('so_dien_thoai', '')
        obj.email = data.get('email', '')
        obj.han_muc_cong_no = data.get('han_muc_cong_no', 0) or 0
        obj.so_ngay_no_max = data.get('so_ngay_no_max', 0) or 0
        obj.chiet_khau_mac_dinh = data.get('chiet_khau_mac_dinh', 0) or 0
        obj.ghi_chu = data.get('ghi_chu', '')
        try:
            obj.save()
            messages.success(request, f'Đã lưu khách hàng: {obj.ten_kh}')
            return redirect('kh_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
    return render(request, 'danh_muc/kh_form.html', {
        'obj': obj,
        'nhom_list': NhomKhachHang.objects.all(),
        'page_title': 'Thêm KH' if not pk else 'Sửa KH',
        'active_menu': 'khach_hang',
    })


@login_required
def kh_xoa(request, pk):
    obj = get_object_or_404(KhachHang, pk=pk)
    if request.method == 'POST':
        obj.trang_thai = False
        obj.save()
        messages.success(request, 'Đã xóa khách hàng')
    return redirect('kh_list')


# ─── NHÀ CUNG CẤP ────────────────────────────────────────────
@login_required
def ncc_list(request):
    q = request.GET.get('q', '')
    items = NhaCungCap.objects.filter(trang_thai=True)
    if q:
        items = items.filter(Q(ma_ncc__icontains=q) | Q(ten_ncc__icontains=q) |
                             Q(so_dien_thoai__icontains=q))
    return render(request, 'danh_muc/ncc_list.html', {
        'items': items, 'q': q,
        'page_title': 'Nhà cung cấp', 'active_menu': 'nha_cung_cap',
    })


@login_required
def ncc_form(request, pk=None):
    obj = get_object_or_404(NhaCungCap, pk=pk) if pk else None
    if request.method == 'POST':
        data = request.POST
        if not obj:
            obj = NhaCungCap()
        obj.ma_ncc = data.get('ma_ncc', '').strip()
        obj.ten_ncc = data.get('ten_ncc', '').strip()
        obj.loai_ncc = data.get('loai_ncc', 'dai_ly')
        obj.ma_so_thue = data.get('ma_so_thue', '')
        obj.dia_chi = data.get('dia_chi', '')
        obj.so_dien_thoai = data.get('so_dien_thoai', '')
        obj.email = data.get('email', '')
        obj.nguoi_lien_he = data.get('nguoi_lien_he', '')
        obj.so_tk_ngan_hang = data.get('so_tk_ngan_hang', '')
        obj.ngan_hang = data.get('ngan_hang', '')
        obj.so_ngay_thanh_toan = data.get('so_ngay_thanh_toan', 30) or 30
        obj.ghi_chu = data.get('ghi_chu', '')
        try:
            obj.save()
            messages.success(request, f'Đã lưu NCC: {obj.ten_ncc}')
            return redirect('ncc_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
    return render(request, 'danh_muc/ncc_form.html', {
        'obj': obj,
        'page_title': 'Thêm NCC' if not pk else 'Sửa NCC',
        'active_menu': 'nha_cung_cap',
    })


@login_required
def ncc_xoa(request, pk):
    obj = get_object_or_404(NhaCungCap, pk=pk)
    if request.method == 'POST':
        obj.trang_thai = False
        obj.save()
        messages.success(request, 'Đã xóa NCC')
    return redirect('ncc_list')
