"""Views cho app Kho: PhieuXuat, TonKho, KiemKe, SoDo, TinhGia, DoiChieu"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import PhieuNhap, PhieuNhap_CT, PhieuXuat, PhieuXuat_CT, TonKho, KiemKe, KiemKe_CT
from apps.core.models import HangHoa, Kho
from apps.danh_muc.models import NhaCungCap


def _gen_so_phieu(prefix):
    now = timezone.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"


# ─── TỒN KHO ────────────────────────────────────────────────
@login_required
def ton_kho_list(request):
    kho_id = request.GET.get('kho', '')
    q = request.GET.get('q', '')
    items = TonKho.objects.select_related('hang_hoa', 'kho',
                                          'hang_hoa__nhom_hang', 'hang_hoa__don_vi_tinh',
                                          'hang_hoa__thuong_hieu')
    if kho_id:
        items = items.filter(kho_id=kho_id)
    if q:
        items = items.filter(
            Q(hang_hoa__ma_hang__icontains=q) | Q(hang_hoa__ten_hang__icontains=q))
    items = items.order_by('hang_hoa__ma_hang')

    # Thêm giá trị tính toán
    all_items = TonKho.objects.select_related('hang_hoa')
    tong_gia_tri = sum(t.so_luong * t.gia_von_tb for t in all_items)
    so_hang_can_nhap = all_items.filter(so_luong__lte=0).count()
    tong_chung_lo = all_items.count()

    context = {
        'items': items,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_id,
        'q': q,
        'tong_gia_tri': int(tong_gia_tri),
        'so_hang_can_nhap': so_hang_can_nhap,
        'tong_chung_lo': tong_chung_lo,
        'tong_kho': Kho.objects.filter(trang_thai=True).count(),
        'page_title': 'Tồn kho hiện tại',
        'active_menu': 'ton_kho',
    }
    return render(request, 'kho/ton_kho_list.html', context)


# ─── SƠ ĐỒ KHO ──────────────────────────────────────────────
@login_required
def so_do_kho(request):
    kho_sel = request.GET.get('kho_id', '')
    kho_all = Kho.objects.filter(trang_thai=True)

    # Thêm thống kê số mặt hàng cho mỗi kho
    kho_list = []
    for k in kho_all:
        k.so_mat_hang = TonKho.objects.filter(kho=k, so_luong__gt=0).count()
        kho_list.append(k)

    items = TonKho.objects.select_related(
        'hang_hoa', 'kho', 'hang_hoa__nhom_hang',
        'hang_hoa__don_vi_tinh', 'hang_hoa__thuong_hieu'
    ).filter(so_luong__gte=0).order_by('kho__ma_kho', 'hang_hoa__ma_hang')

    if kho_sel:
        items = items.filter(kho_id=kho_sel)

    return render(request, 'kho/so_do_kho.html', {
        'kho_list': kho_list,
        'items': items,
        'kho_sel': kho_sel,
        'page_title': 'Sơ đồ kho',
        'active_menu': 'so_do_kho',
    })


# ─── TÍNH GIÁ XUẤT KHO ──────────────────────────────────────
@login_required
def tinh_gia_xuat(request):
    kho_filter = request.GET.get('kho', '')
    items = TonKho.objects.select_related(
        'hang_hoa', 'kho', 'hang_hoa__nhom_hang', 'hang_hoa__don_vi_tinh'
    ).order_by('hang_hoa__ma_hang')

    if kho_filter:
        items = items.filter(kho_id=kho_filter)

    tong_gia_tri_ton = sum(t.so_luong * t.gia_von_tb for t in items)
    thang = timezone.now().strftime('%m/%Y')

    # Thống kê xuất kho tháng này
    now = timezone.now()
    first_day = now.replace(day=1)
    tong_phieu_xuat = PhieuXuat.objects.filter(
        ngay_xuat__gte=first_day.date(), trang_thai='da_xuat'
    ).count()
    tong_gia_von_xuat = PhieuXuat.objects.filter(
        ngay_xuat__gte=first_day.date(), trang_thai='da_xuat'
    ).aggregate(t=Sum('tong_gia_von'))['t'] or 0

    return render(request, 'kho/tinh_gia_xuat.html', {
        'items': items,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_filter,
        'tong_gia_tri_ton': int(tong_gia_tri_ton),
        'tong_phieu_xuat': tong_phieu_xuat,
        'tong_gia_von_xuat': int(tong_gia_von_xuat),
        'tong_ton_kho': int(tong_gia_tri_ton),
        'thang': thang,
        'page_title': 'Tính giá xuất kho',
        'active_menu': 'tinh_gia_xuat',
    })


# ─── ĐỐI CHIẾU SỐ LIỆU ──────────────────────────────────────
@login_required
def doi_chieu_so_lieu(request):
    today = date.today()
    tu_ngay = request.GET.get('tu_ngay', today.replace(day=1).isoformat())
    den_ngay = request.GET.get('den_ngay', today.isoformat())
    kho_filter = request.GET.get('kho', '')

    # Tổng giá vốn xuất từ phiếu xuất trong kỳ
    xuat_qs = PhieuXuat.objects.filter(
        ngay_xuat__range=[tu_ngay, den_ngay],
        trang_thai='da_xuat'
    )
    if kho_filter:
        xuat_qs = xuat_qs.filter(kho_id=kho_filter)
    tong_gia_von_xuat = xuat_qs.aggregate(t=Sum('tong_gia_von'))['t'] or 0

    # Tổng giá trị tồn kho hiện tại
    ton_qs = TonKho.objects.select_related('hang_hoa', 'kho')
    if kho_filter:
        ton_qs = ton_qs.filter(kho_id=kho_filter)
    tong_ton_hien_tai = sum(t.so_luong * t.gia_von_tb for t in ton_qs)

    chenh_lech_tong = int(tong_ton_hien_tai) - int(tong_gia_von_xuat)

    # Chi tiết theo mặt hàng
    rows = []
    for tk in ton_qs.order_by('hang_hoa__ma_hang'):
        gv_xuat = PhieuXuat_CT.objects.filter(
            phieu_xuat__ngay_xuat__range=[tu_ngay, den_ngay],
            phieu_xuat__trang_thai='da_xuat',
            hang_hoa=tk.hang_hoa,
        ).aggregate(t=Sum('tong_gia_von'))['t'] or 0

        gv_ton = int(tk.so_luong * tk.gia_von_tb)
        rows.append({
            'ma_hang': tk.hang_hoa.ma_hang,
            'ten_hang': tk.hang_hoa.ten_hang,
            'ten_kho': tk.kho.ten_kho,
            'gv_xuat': int(gv_xuat),
            'gv_ton': gv_ton,
            'chenh_lech': gv_ton - int(gv_xuat),
        })

    return render(request, 'kho/doi_chieu_so_lieu.html', {
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_filter,
        'tong_gia_von_xuat': int(tong_gia_von_xuat),
        'tong_ton_hien_tai': int(tong_ton_hien_tai),
        'chenh_lech_tong': chenh_lech_tong,
        'rows': rows,
        'page_title': 'Đối chiếu số liệu',
        'active_menu': 'doi_chieu_kho',
    })


# ─── PHIẾU NHẬP KHO ────────────────────────────────────────
@login_required
def phieu_nhap_list(request):
    q = request.GET.get('q', '')
    items = PhieuNhap.objects.select_related('nha_cung_cap', 'kho')
    if q:
        items = items.filter(Q(so_phieu__icontains=q) |
                             Q(nha_cung_cap__ten_ncc__icontains=q))
    context = {
        'items': items[:50],
        'q': q,
        'page_title': 'Phiếu nhập kho',
        'active_menu': 'phieu_nhap',
    }
    return render(request, 'kho/phieu_nhap_list.html', context)


@login_required
def phieu_nhap_them(request):
    if request.method == 'POST':
        data = request.POST
        so_phieu = data.get('so_phieu') or _gen_so_phieu('NK')
        phieu = PhieuNhap.objects.create(
            so_phieu=so_phieu,
            ngay_nhap=data.get('ngay_nhap') or date.today(),
            loai_nhap=data.get('loai_nhap', 'mua_ncc'),
            nha_cung_cap_id=data.get('ncc') or None,
            so_hd_ncc=data.get('so_hd_ncc', ''),
            ngay_hd_ncc=data.get('ngay_hd_ncc') or None,
            kho_id=data.get('kho'),
            ghi_chu=data.get('ghi_chu', ''),
            nguoi_tao=request.user,
        )
        # Xử lý chi tiết
        hang_ids = data.getlist('hang_id[]')
        sl_nhans = data.getlist('sl_nhan[]')
        don_gias = data.getlist('don_gia[]')
        vats = data.getlist('vat[]')
        for i in range(len(hang_ids)):
            if hang_ids[i] and sl_nhans[i] and don_gias[i]:
                PhieuNhap_CT.objects.create(
                    phieu_nhap=phieu,
                    hang_hoa_id=hang_ids[i],
                    so_luong_nhan=int(sl_nhans[i]),
                    don_gia=float(don_gias[i]),
                    thue_vat=float(vats[i]) if vats[i] else 10,
                )
        phieu.tinh_tong()
        messages.success(request, f'Đã tạo phiếu nhập {phieu.so_phieu}')
        return redirect('phieu_nhap_detail', pk=phieu.pk)

    context = {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'so_phieu_default': _gen_so_phieu('NK'),
        'today': date.today(),
        'page_title': 'Tạo phiếu nhập kho',
        'active_menu': 'phieu_nhap',
    }
    return render(request, 'kho/phieu_nhap_form.html', context)


@login_required
def phieu_nhap_detail(request, pk):
    phieu = get_object_or_404(PhieuNhap, pk=pk)
    chi_tiet = phieu.chi_tiet.select_related('hang_hoa')
    context = {
        'phieu': phieu,
        'chi_tiet': chi_tiet,
        'page_title': f'Phiếu nhập {phieu.so_phieu}',
        'active_menu': 'phieu_nhap',
    }
    return render(request, 'kho/phieu_nhap_detail.html', context)


@login_required
def phieu_nhap_xac_nhan(request, pk):
    phieu = get_object_or_404(PhieuNhap, pk=pk)
    if request.method == 'POST':
        ok = phieu.xac_nhan_nhap_kho()
        if ok:
            messages.success(request, f'Đã nhập kho thành công: {phieu.so_phieu}')
        else:
            messages.error(request, 'Không thể xác nhận - phiếu đã được xử lý')
    return redirect('phieu_nhap_detail', pk=pk)


# ─── PHIẾU XUẤT KHO ────────────────────────────────────────
@login_required
def phieu_xuat_list(request):
    q = request.GET.get('q', '')
    items = PhieuXuat.objects.select_related('kho')
    if q:
        items = items.filter(so_phieu__icontains=q)
    context = {
        'items': items[:50],
        'q': q,
        'page_title': 'Phiếu xuất kho',
        'active_menu': 'phieu_xuat',
    }
    return render(request, 'kho/phieu_xuat_list.html', context)


@login_required
def phieu_xuat_them(request):
    if request.method == 'POST':
        data = request.POST
        kho_id = data.get('kho')
        phieu = PhieuXuat.objects.create(
            so_phieu=data.get('so_phieu') or _gen_so_phieu('XK'),
            ngay_xuat=data.get('ngay_xuat') or date.today(),
            loai_xuat=data.get('loai_xuat', 'noi_bo'),
            kho_id=kho_id,
            trang_thai='da_xuat',
            nguoi_tao=request.user,
            ghi_chu=data.get('ghi_chu', ''),
        )
        hang_ids = data.getlist('hang_id[]')
        so_luongs = data.getlist('so_luong[]')
        tong_gv = 0
        for i in range(len(hang_ids)):
            if hang_ids[i] and so_luongs[i]:
                h_id = int(hang_ids[i])
                sl = int(so_luongs[i])
                tk = TonKho.objects.filter(hang_hoa_id=h_id, kho_id=kho_id).first()
                gv = tk.gia_von_tb if tk else 0
                tgv = gv * sl
                PhieuXuat_CT.objects.create(
                    phieu_xuat=phieu, hang_hoa_id=h_id,
                    so_luong=sl, gia_von=gv, tong_gia_von=tgv
                )
                if tk and tk.so_luong >= sl:
                    tk.so_luong -= sl
                    tk.save()
                tong_gv += tgv
        phieu.tong_gia_von = tong_gv
        phieu.save(update_fields=['tong_gia_von'])
        messages.success(request, f'Đã tạo phiếu xuất {phieu.so_phieu}')
        return redirect('phieu_xuat_list')

    context = {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'so_phieu_default': _gen_so_phieu('XK'),
        'today': date.today(),
        'page_title': 'Tạo phiếu xuất kho',
        'active_menu': 'phieu_xuat',
    }
    return render(request, 'kho/phieu_xuat_form.html', context)


# ─── KIỂM KÊ ────────────────────────────────────────────────
@login_required
def kiem_ke_list(request):
    items = KiemKe.objects.select_related('kho').order_by('-ngay_kiem_ke')[:20]
    return render(request, 'kho/kiem_ke_list.html', {
        'items': items, 'page_title': 'Phiếu kiểm kê', 'active_menu': 'kiem_ke'
    })


@login_required
def kiem_ke_them(request):
    if request.method == 'POST':
        kho_id = request.POST.get('kho')
        kk = KiemKe.objects.create(
            ngay_kiem_ke=request.POST.get('ngay') or date.today(),
            kho_id=kho_id,
            nguoi_kiem=request.POST.get('nguoi_kiem', ''),
            ghi_chu=request.POST.get('ghi_chu', ''),
        )
        # Tự động tạo danh sách từ tồn kho hiện tại
        for tk in TonKho.objects.filter(kho_id=kho_id):
            KiemKe_CT.objects.create(
                kiem_ke=kk,
                hang_hoa=tk.hang_hoa,
                so_luong_so_sach=tk.so_luong,
                so_luong_thuc_te=tk.so_luong,
            )
        messages.success(request, 'Đã tạo phiếu kiểm kê')
        return redirect('kiem_ke_detail', pk=kk.pk)
    return render(request, 'kho/kiem_ke_form.html', {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'today': date.today(),
        'page_title': 'Tạo phiếu kiểm kê',
        'active_menu': 'kiem_ke',
    })


@login_required
def kiem_ke_detail(request, pk):
    kk = get_object_or_404(KiemKe, pk=pk)
    chi_tiet = kk.chi_tiet.select_related('hang_hoa')
    if request.method == 'POST' and kk.trang_thai == 'dang_kiem':
        ct_ids = request.POST.getlist('ct_id[]')
        sl_thuc_tes = request.POST.getlist('sl_thuc_te[]')
        for i, ct_id in enumerate(ct_ids):
            ct = KiemKe_CT.objects.get(pk=ct_id)
            ct.so_luong_thuc_te = int(sl_thuc_tes[i])
            ct.save()
        messages.success(request, 'Đã lưu số liệu kiểm kê')
        return redirect('kiem_ke_detail', pk=pk)
    return render(request, 'kho/kiem_ke_detail.html', {
        'kk': kk, 'chi_tiet': chi_tiet,
        'page_title': f'Kiểm kê {kk.kho.ten_kho}',
        'active_menu': 'kiem_ke',
    })


# ─── BÁO CÁO KHO ────────────────────────────────────────────
@login_required
def bao_cao_ton_kho(request):
    kho_id = request.GET.get('kho', '')
    items = TonKho.objects.select_related(
        'hang_hoa', 'hang_hoa__nhom_hang', 'kho'
    ).order_by('hang_hoa__nhom_hang', 'hang_hoa__ma_hang')
    if kho_id:
        items = items.filter(kho_id=kho_id)
    tong_gia_tri = sum(t.so_luong * t.gia_von_tb for t in items)
    return render(request, 'kho/bao_cao_ton.html', {
        'items': items,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_id,
        'tong_gia_tri': tong_gia_tri,
        'page_title': 'Báo cáo tồn kho',
        'active_menu': 'bao_cao_kho',
    })
