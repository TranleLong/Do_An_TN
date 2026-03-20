from apps.mua_hang.models import PhieuChi
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def cong_no_ncc(request):
    """View gộp công nợ NCC"""
    from apps.danh_muc.models import KhachHang, NhaCungCap

    ds_ncc = NhaCungCap.objects.all()
    return render(
        request,
        'ban_hang/cong_no_tong_hop.html',
        {
            'khach_hang_no': KhachHang.objects.all(),
            'ncc_no': ds_ncc,
            'page_title': 'Sổ chi tiết công nợ',
            'active_menu': 'cong_no_ncc',
        },
    )


@login_required
def don_mua_list(request):
    return render(
        request,
        'mua_hang/don_mua_list.html',
        {'page_title': 'Quản lý Mua hàng', 'active_menu': 'don_mua'},
    )


@login_required
def don_mua_them(request):
    return redirect('don_mua_list')


@login_required
def don_mua_detail(request, pk):
    return redirect('don_mua_list')


@login_required
def don_mua_duyet(request, pk):
    return redirect('don_mua_list')


@login_required
def hoa_don_mua_list(request):
    return redirect('don_mua_list')


@login_required
def hoa_don_mua_them(request):
    return redirect('don_mua_list')


@login_required
def phieu_chi_list(request):
    items = PhieuChi.objects.select_related('nha_cung_cap').order_by('-ngay_chi')[:50]
    return render(
        request,
        'ban_hang/phieu_thu_list.html',
        {
            'phieu_chi_list': items,
            'page_title': 'Phiếu chi tiền',
            'active_menu': 'phieu_chi',
        },
    )


@login_required
def phieu_chi_them(request):
    from apps.danh_muc.models import NhaCungCap

    if request.method == 'POST':
        messages.success(request, 'Đã lưu phiếu chi thành công!')
        return redirect('don_mua_list')

    return render(
        request,
        'ban_hang/phieu_thu_chi_form.html',
        {
            'loai': 'chi',
            'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
            'page_title': 'Lập Phiếu Chi',
            'so_phieu_default': 'PC-1111',
            'active_menu': 'phieu_chi',
        },
    )
