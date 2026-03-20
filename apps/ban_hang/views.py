"""Views cho app Bán Hàng"""
from datetime import date
from decimal import Decimal, InvalidOperation

from apps.core.models import HangHoa, Kho
from apps.danh_muc.models import KhachHang
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import DonBan, DonBan_CT, PhieuThu


def _gen_so_don(prefix):
    now = timezone.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"


# ─── ĐƠN BÁN HÀNG ───────────────────────────────────────────
@login_required
def don_ban_list(request):
    q = request.GET.get('q', '')
    trang_thai = request.GET.get('trang_thai', '')
    items = DonBan.objects.select_related('khach_hang', 'kho')
    if q:
        items = items.filter(Q(so_don__icontains=q) | Q(ten_kh__icontains=q) |
                             Q(sdt_kh__icontains=q))
    if trang_thai:
        items = items.filter(trang_thai=trang_thai)
    context = {
        'items': items[:50],
        'q': q,
        'trang_thai_filter': trang_thai,
        'page_title': 'Đơn bán hàng',
        'active_menu': 'don_ban',
    }
    return render(request, 'ban_hang/don_ban_list.html', context)


@login_required
def don_ban_them(request):
    if request.method == 'POST':
        data = request.POST
        kh_id = data.get('khach_hang') or None
        kh = KhachHang.objects.filter(pk=kh_id).first() if kh_id else None
        loai_ban = data.get('loai_ban', 'ban_le')
        phuong_thuc_tt = data.get('phuong_thuc_tt')
        if not phuong_thuc_tt:
            phuong_thuc_tt = 'tien_mat' if loai_ban == 'ban_le' else 'no'

        don = DonBan.objects.create(
            so_don=data.get('so_don') or _gen_so_don('BH'),
            ngay_ban=data.get('ngay_ban') or date.today(),
            loai_ban=loai_ban,
            khach_hang=kh,
            ten_kh=data.get('ten_kh') or (kh.ten_kh if kh else 'Khách lẻ'),
            sdt_kh=data.get('sdt_kh', ''),
            xe_kh=data.get('xe_kh', ''),
            kho_id=data.get('kho'),
            nhan_vien_ban=request.user,
            phuong_thuc_tt=phuong_thuc_tt,
            chiet_khau_dh=Decimal(data.get('chiet_khau_dh', 0) or 0),
            ghi_chu=data.get('ghi_chu', ''),
        )

        hang_ids = data.getlist('hang_id[]')
        so_luongs = data.getlist('so_luong[]')
        don_gias = data.getlist('don_gia[]')
        cks = data.getlist('chiet_khau[]')
        vats = data.getlist('vat[]')

        so_dong_hop_le = 0
        for i in range(len(hang_ids)):
            if hang_ids[i] and so_luongs[i] and don_gias[i]:
                so_luong = int(so_luongs[i])
                don_gia = Decimal(don_gias[i])
                if so_luong <= 0 or don_gia < 0:
                    continue

                DonBan_CT.objects.create(
                    don_ban=don,
                    hang_hoa_id=hang_ids[i],
                    so_luong=so_luong,
                    don_gia=don_gia,
                    chiet_khau=Decimal(cks[i]) if cks[i] else Decimal('0'),
                    thue_vat=Decimal(vats[i]) if vats[i] else Decimal('10'),
                )
                so_dong_hop_le += 1

        if so_dong_hop_le == 0:
            don.delete()
            messages.error(request, 'Đơn bán phải có ít nhất 1 dòng hàng hóa hợp lệ')
            return redirect('don_ban_them')

        don.tinh_tong()
        messages.success(request, f'Đã tạo đơn {don.so_don}')
        return redirect('don_ban_detail', pk=don.pk)

    context = {
        'kh_list': KhachHang.objects.filter(trang_thai=True),
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'so_don_default': _gen_so_don('BH'),
        'today': date.today(),
        'page_title': 'Tạo đơn bán hàng',
        'active_menu': 'don_ban',
    }
    return render(request, 'ban_hang/don_ban_form.html', context)


@login_required
def don_ban_detail(request, pk):
    don = get_object_or_404(DonBan, pk=pk)
    chi_tiet = don.chi_tiet.select_related('hang_hoa')
    context = {
        'don': don,
        'chi_tiet': chi_tiet,
        'page_title': f'Đơn bán {don.so_don}',
        'active_menu': 'don_ban',
    }
    return render(request, 'ban_hang/don_ban_detail.html', context)


@login_required
def don_ban_xac_nhan(request, pk):
    don = get_object_or_404(DonBan, pk=pk)
    if request.method == 'POST':
        ok, msg = don.xac_nhan_don_ban()
        if ok:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('don_ban_detail', pk=pk)


@login_required
def don_ban_huy(request, pk):
    don = get_object_or_404(DonBan, pk=pk)
    if request.method == 'POST' and don.trang_thai == 'nhap':
        don.trang_thai = 'huy'
        don.save()
        messages.success(request, f'Đã hủy đơn {don.so_don}')
    return redirect('don_ban_list')


# ─── PHIẾU THU ──────────────────────────────────────────────
@login_required
def phieu_thu_list(request):
    items = PhieuThu.objects.select_related('khach_hang').order_by('-ngay_thu')[:50]
    return render(request, 'ban_hang/phieu_thu_list.html', {
        'items': items, 'page_title': 'Phiếu thu tiền', 'active_menu': 'phieu_thu'
    })


@login_required
def phieu_thu_them(request):
    if request.method == 'POST':
        data = request.POST
        don_id = data.get('don_ban') or None
        don = DonBan.objects.filter(pk=don_id).first() if don_id else None

        try:
            tong_thu = Decimal(data.get('tong_thu', 0) or 0)
        except InvalidOperation:
            messages.error(request, 'Số tiền thu không hợp lệ')
            return redirect('phieu_thu_them')

        if tong_thu <= 0:
            messages.error(request, 'Số tiền thu phải lớn hơn 0')
            return redirect('phieu_thu_them')

        if don and don.trang_thai != 'da_xac_nhan':
            messages.error(request, 'Chỉ thu tiền cho đơn đã xác nhận')
            return redirect('phieu_thu_them')

        if don and tong_thu > don.con_no:
            messages.error(request, f'Số tiền thu vượt công nợ còn lại ({don.con_no:,.0f} đ)')
            return redirect('phieu_thu_them')

        pt = PhieuThu.objects.create(
            so_phieu=data.get('so_phieu') or _gen_so_don('PT'),
            ngay_thu=data.get('ngay_thu') or date.today(),
            khach_hang_id=data.get('khach_hang'),
            hinh_thuc_thu=data.get('hinh_thuc_thu', 'tien_mat'),
            so_tham_chieu=data.get('so_tham_chieu', ''),
            tong_thu=tong_thu,
            don_ban=don,
            ghi_chu=data.get('ghi_chu', ''),
            nguoi_tao=request.user,
        )
        # Cập nhật đã thu vào đơn bán
        if don:
            don.da_thu += pt.tong_thu
            don.con_no = don.tong_thanh_toan - don.da_thu
            don.save(update_fields=['da_thu', 'con_no'])
        messages.success(request, f'Đã tạo phiếu thu {pt.so_phieu}')
        return redirect('phieu_thu_list')

    don_id = request.GET.get('don_ban')
    don = DonBan.objects.filter(pk=don_id).first() if don_id else None
    return render(request, 'ban_hang/phieu_thu_form.html', {
        'kh_list': KhachHang.objects.filter(trang_thai=True),
        'don_ban_list': DonBan.objects.filter(trang_thai='da_xac_nhan').exclude(con_no=0),
        'don_selected': don,
        'so_phieu_default': _gen_so_don('PT'),
        'today': date.today(),
        'page_title': 'Lập phiếu thu tiền',
        'active_menu': 'phieu_thu',
    })


# ─── BÁO CÁO BÁN HÀNG ───────────────────────────────────────
@login_required
def bao_cao_doanh_thu(request):
    from_date = request.GET.get('from_date', date.today().replace(day=1).isoformat())
    to_date = request.GET.get('to_date', date.today().isoformat())
    items = DonBan.objects.filter(
        trang_thai='da_xac_nhan',
        ngay_ban__gte=from_date,
        ngay_ban__lte=to_date,
    ).select_related('khach_hang', 'nhan_vien_ban')
    tong_dt = items.aggregate(t=Sum('tong_thanh_toan'))['t'] or 0
    tong_gv = sum(
        ct.gia_von * ct.so_luong
        for don in items
        for ct in don.chi_tiet.all()
    )
    context = {
        'items': items,
        'from_date': from_date,
        'to_date': to_date,
        'tong_dt': tong_dt,
        'tong_gv': tong_gv,
        'loi_nhuan': tong_dt - tong_gv,
        'page_title': 'Báo cáo doanh thu',
        'active_menu': 'bao_cao_bh',
    }
    return render(request, 'ban_hang/bao_cao_doanh_thu.html', context)


# ─── CÔNG NỢ KHÁCH HÀNG ─────────────────────────────────────
@login_required
def cong_no_kh(request):
    kh_list = KhachHang.objects.filter(trang_thai=True)
    data = []
    for kh in kh_list:
        no = kh.get_cong_no()
        if no > 0:
            data.append({'kh': kh, 'no': no})
    return render(request, 'ban_hang/cong_no_kh.html', {
        'data': data, 'page_title': 'Công nợ khách hàng', 'active_menu': 'cong_no_kh'
    })
