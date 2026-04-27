"""Views cho app Danh Mục: KhachHang, NhaCungCap"""
import json
import re
from datetime import date, timedelta
from urllib.error import URLError
from urllib.request import urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Length
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.ban_hang.models import DonBan

from .models import (DonViTinh, HangHoa, KhachHang, Kho, NhaCungCap, NhomHang,
                     NhomKhachHang, TaiKhoanKeToan, ThuongHieu, ViTriKho)

PHONE_REGEX = re.compile(r"^(0|\+84)[0-9]{9,10}$")
SLOT_TAG_REGEX = re.compile(r"\[SLOT=(?P<size>[1-5])\]")
KHO_SO_DAY = 3
KHO_KE_MOI_DAY = 4
KHO_VI_TRI_MOI_KE = 5


def _is_valid_phone(phone):
    return bool(PHONE_REGEX.match((phone or "").strip()))


def _parse_int_field(value, default=0):
    text = re.sub(r'[^0-9-]', '', str(value or '').strip())
    if text in ('', '-'): 
        return default
    try:
        return int(text)
    except ValueError:
        return default


def _parse_decimal_field(value, default=0):
    val_str = str(value or '').strip()
    if not val_str:
        return default
    text = val_str.replace('.', '').replace(',', '.')
    text = re.sub(r'[^0-9.-]', '', text)
    if text in ('', '-', '.', '-.'):
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _build_protected_error_message(exc, default_message='Không thể xóa vì còn dữ liệu liên quan.'):
    protected = list(getattr(exc, 'protected_objects', []) or [])
    if not protected:
        return default_message

    labels = []
    for obj in protected[:5]:
        meta = getattr(obj, '_meta', None)
        model_name = meta.verbose_name if meta else obj.__class__.__name__
        labels.append(f'{model_name}: {obj}')
    if len(protected) > 5:
        labels.append('...')
    return f"{default_message} ({'; '.join(labels)})"


def _normalize_tax_code(code):
    return re.sub(r'[^0-9]', '', (code or '').strip())


def _lookup_tax_code_external(ma_so_thue):
    """Tra cứu MST từ nguồn công khai khi nội bộ chưa có dữ liệu."""
    normalized = _normalize_tax_code(ma_so_thue)
    if not normalized:
        return None

    url = f'https://esgoo.net/api-mst/{normalized}.htm'
    try:
        with urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    data = payload.get('data')
    if not isinstance(data, dict):
        return None

    ten_kh = (data.get('ten') or '').strip()
    dia_chi = (data.get('dc') or '').strip()
    so_dien_thoai = (data.get('dt') or '').strip()
    mst = (data.get('mst') or normalized).strip()

    if not ten_kh:
        return None

    return {
        'id': None,
        'ma_kh': '',
        'ten_kh': ten_kh,
        'loai_kh': '2',
        'ma_so_thue': mst,
        'dia_chi': '' if dia_chi.lower() == 'null' else dia_chi,
        'so_dien_thoai': '' if so_dien_thoai.lower() == 'null' else so_dien_thoai,
        'email': '',
        'nhom_kh_id': '',
        'han_muc_cong_no': 0,
        'so_ngay_no_max': 0,
        'chiet_khau_mac_dinh': 0,
        'ghi_chu': '',
        'lookup_source': 'tax-api',
    }


def _generate_next_ma_kh():
    """Sinh mã KH tiếp theo theo định dạng KH00001, KH00002, ..."""
    prefix = 'KH'
    max_index = 0
    for code in KhachHang.objects.filter(ma_kh__istartswith=prefix).values_list('ma_kh', flat=True):
        text = str(code or '').strip().upper()
        if not text.startswith(prefix):
            continue
        suffix = text[len(prefix):]
        if suffix.isdigit():
            max_index = max(max_index, int(suffix))
    return f'{prefix}{max_index + 1:05d}'


def _generate_next_ma_hang():
    """Sinh mã hàng tiếp theo theo định dạng HH00001, HH00002, ..."""
    prefix = 'HH'
    max_index = 0
    for code in HangHoa.objects.filter(ma_hang__istartswith=prefix).values_list('ma_hang', flat=True):
        text = str(code or '').strip().upper()
        if not text.startswith(prefix):
            continue
        suffix = text[len(prefix):]
        if suffix.isdigit():
            max_index = max(max_index, int(suffix))
    return f'{prefix}{max_index + 1:05d}'


def _generate_next_ma_nhom():
    """Sinh mã nhóm tiếp theo theo định dạng NH00001, NH00002, ..."""
    prefix = 'NH'
    max_index = 0
    for code in NhomHang.objects.filter(ma_nhom__istartswith=prefix).values_list('ma_nhom', flat=True):
        text = str(code or '').strip().upper()
        if not text.startswith(prefix):
            continue
        suffix = text[len(prefix):]
        if suffix.isdigit():
            max_index = max(max_index, int(suffix))
    return f'{prefix}{max_index + 1:05d}'


def _extract_slot_size_and_note(ghi_chu):
    note = (ghi_chu or '').strip()
    m = SLOT_TAG_REGEX.search(note)
    size = int(m.group('size')) if m else 1
    clean_note = SLOT_TAG_REGEX.sub('', note).strip()
    return size, clean_note


def _merge_slot_size_and_note(slot_size, note_text):
    note_text = (note_text or '').strip()
    tag = f"[SLOT={slot_size}]"
    return f"{tag} {note_text}".strip()


def _paginate_queryset(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def _render_kh_form(request, obj, pk):
    return render(
        request,
        "danh_muc/kh_form.html",
        {
            "obj": obj,
            "nhom_list": NhomKhachHang.objects.all(),
            "page_title": "Thêm KH" if not pk else "Sửa KH",
            "active_menu": "khach_hang",
        },
    )


def _sync_supplier_from_customer(khach_hang):
    if not khach_hang.la_nha_cung_cap:
        NhaCungCap.objects.filter(ma_ncc=khach_hang.ma_kh).update(trang_thai=False)
        return

    NhaCungCap.objects.update_or_create(
        ma_ncc=khach_hang.ma_kh,
        defaults={
            'ten_ncc': khach_hang.ten_kh,
            'loai_ncc': 'dai_ly',
            'ma_so_thue': khach_hang.ma_so_thue,
            'dia_chi': khach_hang.dia_chi,
            'so_dien_thoai': khach_hang.so_dien_thoai,
            'email': khach_hang.email,
            'nguoi_lien_he': khach_hang.ten_kh,
            'so_ngay_thanh_toan': khach_hang.so_ngay_no_max or 30,
            'ghi_chu': khach_hang.ghi_chu,
            'trang_thai': True,
        },
    )


@login_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    try:
        tong_hang_hoa = HangHoa.objects.filter(trang_thai='dang_ban').count()
        tong_kh = KhachHang.objects.filter(trang_thai=True).count()
        tong_ncc = NhaCungCap.objects.filter(trang_thai=True).count()

        doanh_thu_thang = DonBan.objects.filter(
            trang_thai__in=['2', '3'], ngay_chung_tu__gte=month_start
        ).aggregate(total=Sum('tong_thanh_toan'))['total'] or 0

        don_ban_hom_nay = DonBan.objects.filter(ngay_chung_tu=today).count()

        hang_sap_het = []
        for h in HangHoa.objects.filter(trang_thai='dang_ban'):
            ton = h.get_ton_kho()
            if ton <= h.ton_toi_thieu:
                hang_sap_het.append({'hang': h, 'ton': ton})
        hang_sap_het = hang_sap_het[:8]

        don_ban_gan_day = DonBan.objects.select_related('khach_hang').order_by('-ngay_tao')[:8]

        chart_labels = []
        chart_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            label = d.strftime('%d/%m')
            dt = DonBan.objects.filter(
                trang_thai__in=['2', '3'], ngay_chung_tu=d
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

    return render(request, 'dashboard.html', {
        'tong_hang_hoa': tong_hang_hoa,
        'tong_kh': tong_kh,
        'tong_ncc': tong_ncc,
        'doanh_thu_thang': doanh_thu_thang,
        'don_ban_hom_nay': don_ban_hom_nay,
        'hang_sap_het': hang_sap_het,
        'don_ban_gan_day': don_ban_gan_day,
        'chart_labels': ','.join(chart_labels),
        'chart_data': ','.join(str(x) for x in chart_data),
        'page_title': 'Trang chủ',
        'active_menu': 'dashboard',
    })


# ─── KHÁCH HÀNG ──────────────────────────────────────────────
@login_required
def kh_list(request):
    q = request.GET.get('q', '').strip()
    ma_kh = request.GET.get('ma_kh', '').strip()
    ten_kh = request.GET.get('ten_kh', '').strip()
    so_dien_thoai = request.GET.get('so_dien_thoai', '').strip()
    loai_kh = request.GET.get('loai_kh', '').strip()
    trang_thai = request.GET.get('trang_thai', '1').strip()

    items = KhachHang.objects.all()

    if trang_thai in ('0', '1'):
        items = items.filter(trang_thai=(trang_thai == '1'))

    if q:
        items = items.filter(Q(ma_kh__icontains=q) | Q(ten_kh__icontains=q) |
                             Q(so_dien_thoai__icontains=q))
    if ma_kh:
        items = items.filter(ma_kh__icontains=ma_kh)
    if ten_kh:
        items = items.filter(ten_kh__icontains=ten_kh)
    if so_dien_thoai:
        items = items.filter(so_dien_thoai__icontains=so_dien_thoai)
    if loai_kh:
        items = items.filter(loai_kh=loai_kh)

    page_obj = _paginate_queryset(request, items.order_by('-id'))

    return render(request, 'danh_muc/kh_list.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'q': q,
        'ma_kh': ma_kh,
        'ten_kh': ten_kh,
        'so_dien_thoai': so_dien_thoai,
        'loai_kh': loai_kh,
        'trang_thai': trang_thai,
        'page_title': 'Danh sách khách hàng', 'active_menu': 'khach_hang',
    })


@login_required
def kh_form(request, pk=None):

    # Xử lý copy_from: nếu có tham số copy_from trên URL, lấy dữ liệu khách hàng gốc để đổ vào form tạo mới
    copy_from = request.GET.get('copy_from')
    if pk:
        obj = get_object_or_404(KhachHang, pk=pk)
    elif copy_from:
        kh_copy = get_object_or_404(KhachHang, pk=copy_from)
        obj = KhachHang(
            ma_kh=_generate_next_ma_kh(),
            ten_kh=kh_copy.ten_kh,
            la_khach_hang=kh_copy.la_khach_hang,
            la_nha_cung_cap=kh_copy.la_nha_cung_cap,
            la_nhan_vien=kh_copy.la_nhan_vien,
            loai_kh=kh_copy.loai_kh,
            nhom_kh=kh_copy.nhom_kh,
            ma_so_thue=kh_copy.ma_so_thue,
            dia_chi=kh_copy.dia_chi,
            so_dien_thoai=kh_copy.so_dien_thoai,
            email=kh_copy.email,
            han_muc_cong_no=kh_copy.han_muc_cong_no,
            so_ngay_no_max=kh_copy.so_ngay_no_max,
            chiet_khau_mac_dinh=kh_copy.chiet_khau_mac_dinh,
            ghi_chu=kh_copy.ghi_chu,
        )
    else:
        # Nếu GET request (mở form add), generate mã KH tiếp theo
        obj = KhachHang(ma_kh=_generate_next_ma_kh())
    
    if request.method == 'POST':
        data = request.POST
        if not obj:
            obj = KhachHang()

        # Keep posted values on validation errors for better data-entry UX.
        obj.ma_kh = data.get('ma_kh', '').strip().upper()
        obj.ten_kh = data.get('ten_kh', '').strip()
        obj.la_khach_hang = data.get('la_khach_hang') == 'on'
        obj.la_nha_cung_cap = data.get('la_nha_cung_cap') == 'on'
        obj.la_nhan_vien = data.get('la_nhan_vien') == 'on'
        obj.loai_kh = data.get('loai_kh', '1')
        obj.nhom_kh_id = data.get('nhom_kh') or None
        obj.ma_so_thue = data.get('ma_so_thue', '').strip()
        obj.dia_chi = data.get('dia_chi', '').strip()
        obj.so_dien_thoai = data.get('so_dien_thoai', '').strip()
        obj.email = data.get('email', '').strip()
        obj.han_muc_cong_no = _parse_int_field(data.get('han_muc_cong_no', 0))
        obj.so_ngay_no_max = _parse_int_field(data.get('so_ngay_no_max', 0))
        obj.chiet_khau_mac_dinh = _parse_decimal_field(data.get('chiet_khau_mac_dinh', 0))
        obj.ghi_chu = data.get('ghi_chu', '').strip()

        ma_kh = obj.ma_kh
        ten_kh = obj.ten_kh
        so_dien_thoai = obj.so_dien_thoai
        loai_kh = obj.loai_kh
        ma_so_thue = obj.ma_so_thue
        la_khach_hang = obj.la_khach_hang
        la_nha_cung_cap = obj.la_nha_cung_cap
        la_nhan_vien = obj.la_nhan_vien

        # Kiểm tra trường bắt buộc
        if not ten_kh:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin bắt buộc')
            return _render_kh_form(request, obj, pk)

        # Số điện thoại là tùy chọn; nếu có nhập thì phải đúng định dạng.
        if so_dien_thoai and not _is_valid_phone(so_dien_thoai):
            messages.error(request, 'Số điện thoại không đúng định dạng (bắt đầu bằng 0 hoặc +84, 10-11 chữ số)')
            return _render_kh_form(request, obj, pk)

        if not la_khach_hang and not la_nha_cung_cap and not la_nhan_vien:
            messages.error(request, 'Vui lòng chọn ít nhất 1 vai trò: Khách hàng, Nhà cung cấp hoặc Nhân viên')
            return _render_kh_form(request, obj, pk)

        # Mã số thuế bắt buộc khi chọn Nhà cung cấp hoặc loại 2/3
        if (la_nha_cung_cap or loai_kh in ('2', '3')) and not ma_so_thue:
            message_target = 'Nhà cung cấp' if la_nha_cung_cap else dict(obj.LOAI_KH).get(loai_kh)
            messages.error(request, f'Mã số thuế bắt buộc với loại đối tác: {message_target}')
            return _render_kh_form(request, obj, pk)

        if loai_kh == '2' and not obj.dia_chi:
            messages.error(request, 'Địa chỉ là bắt buộc khi chọn loại khách hàng 2 - Doanh nghiệp')
            return _render_kh_form(request, obj, pk)

        if pk:
            # BR9.2.2-1: không cho phép sửa mã khách hàng
            ma_kh = obj.ma_kh
        else:
            if not ma_kh:
                # Auto-generate nếu không nhập
                ma_kh = _generate_next_ma_kh()
                obj.ma_kh = ma_kh

            # Kiểm tra xem mã KH đã tồn tại chưa
            if KhachHang.objects.filter(ma_kh=ma_kh).exists():
                messages.error(request, 'Mã khách hàng đã tồn tại')
                return _render_kh_form(request, obj, pk)

        obj.ma_kh = ma_kh
        obj.ten_kh = ten_kh
        obj.la_khach_hang = la_khach_hang
        obj.la_nha_cung_cap = la_nha_cung_cap
        obj.la_nhan_vien = la_nhan_vien
        obj.loai_kh = loai_kh
        obj.nhom_kh_id = data.get('nhom_kh') or None
        obj.ma_so_thue = ma_so_thue
        obj.dia_chi = data.get('dia_chi', '').strip()
        obj.so_dien_thoai = so_dien_thoai
        obj.email = data.get('email', '').strip()
        obj.han_muc_cong_no = _parse_int_field(data.get('han_muc_cong_no', 0))
        obj.so_ngay_no_max = _parse_int_field(data.get('so_ngay_no_max', 0))
        obj.chiet_khau_mac_dinh = _parse_decimal_field(data.get('chiet_khau_mac_dinh', 0))
        obj.ghi_chu = data.get('ghi_chu', '').strip()
        try:
            obj.save()
            _sync_supplier_from_customer(obj)
            messages.success(request, f'Đã lưu khách hàng: {obj.ten_kh}')
            return redirect('kh_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')

    return _render_kh_form(request, obj, pk)


@login_required
def kh_xoa(request, pk):
    obj = get_object_or_404(KhachHang, pk=pk)
    if request.method == 'POST':
        da_co_don = DonBan.objects.filter(khach_hang=obj).exists()
        dang_con_no = obj.get_cong_no() > 0

        if da_co_don or dang_con_no:
            messages.error(request, 'Không thể xóa khách hàng đã phát sinh giao dịch')
            return redirect('kh_list')

        obj.trang_thai = False
        obj.save()
        _sync_supplier_from_customer(obj)
        messages.success(request, 'Đã xóa khách hàng')
    return redirect('kh_list')


@login_required
def kh_lich_su_mua_hang(request, pk):
    kh = get_object_or_404(KhachHang, pk=pk)
    so_don = request.GET.get('so_don', '').strip()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    tt_thanh_toan = request.GET.get('tt_thanh_toan', '').strip()

    items = DonBan.objects.filter(khach_hang=kh).order_by('-ngay_chung_tu', '-id')

    if so_don:
        items = items.filter(so_don__icontains=so_don)
    if tu_ngay:
        items = items.filter(ngay_chung_tu__gte=tu_ngay)
    if den_ngay:
        items = items.filter(ngay_chung_tu__lte=den_ngay)
    if trang_thai:
        items = items.filter(trang_thai=trang_thai)
    if tt_thanh_toan == 'da_tt':
        items = items.filter(con_no__lte=0)
    elif tt_thanh_toan == 'chua_tt':
        items = items.filter(con_no__gt=0)

    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'danh_muc/kh_lich_su_mua_hang.html', {
        'kh': kh,
        'items': page_obj,
        'page_obj': page_obj,
        'so_don': so_don,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'trang_thai_filter': trang_thai,
        'tt_thanh_toan': tt_thanh_toan,
        'page_title': f'Lịch sử mua hàng - {kh.ten_kh}',
        'active_menu': 'khach_hang',
    })


@login_required
def kh_lookup_masothue(request):
    """API endpoint để lookup khách hàng theo mã số thuế"""
    ma_so_thue = request.GET.get('ma_so_thue', '').strip()
    normalized_tax_code = _normalize_tax_code(ma_so_thue)
    
    if not normalized_tax_code:
        return JsonResponse({'error': 'Mã số thuế không được để trống'}, status=400)

    try:
        kh = KhachHang.objects.filter(la_khach_hang=True).exclude(ma_so_thue='').get(
            Q(ma_so_thue=ma_so_thue) | Q(ma_so_thue=normalized_tax_code)
        )
        return JsonResponse({
            'id': kh.id,
            'ma_kh': kh.ma_kh,
            'ten_kh': kh.ten_kh,
            'loai_kh': kh.loai_kh,
            'ma_so_thue': kh.ma_so_thue,
            'dia_chi': kh.dia_chi or '',
            'so_dien_thoai': kh.so_dien_thoai or '',
            'email': kh.email or '',
            'nhom_kh_id': kh.nhom_kh_id or '',
            'han_muc_cong_no': float(kh.han_muc_cong_no),
            'so_ngay_no_max': kh.so_ngay_no_max,
            'chiet_khau_mac_dinh': float(kh.chiet_khau_mac_dinh),
            'ghi_chu': kh.ghi_chu or '',
            'lookup_source': 'internal',
        })
    except KhachHang.DoesNotExist:
        for kh in KhachHang.objects.filter(la_khach_hang=True).exclude(ma_so_thue=''):
            if _normalize_tax_code(kh.ma_so_thue) == normalized_tax_code:
                return JsonResponse({
                    'id': kh.id,
                    'ma_kh': kh.ma_kh,
                    'ten_kh': kh.ten_kh,
                    'loai_kh': kh.loai_kh,
                    'ma_so_thue': kh.ma_so_thue,
                    'dia_chi': kh.dia_chi or '',
                    'so_dien_thoai': kh.so_dien_thoai or '',
                    'email': kh.email or '',
                    'nhom_kh_id': kh.nhom_kh_id or '',
                    'han_muc_cong_no': float(kh.han_muc_cong_no),
                    'so_ngay_no_max': kh.so_ngay_no_max,
                    'chiet_khau_mac_dinh': float(kh.chiet_khau_mac_dinh),
                    'ghi_chu': kh.ghi_chu or '',
                    'lookup_source': 'internal',
                })

        external_data = _lookup_tax_code_external(normalized_tax_code)
        if external_data:
            return JsonResponse(external_data)

        return JsonResponse(
            {'error': 'Không tìm thấy khách hàng nội bộ hoặc dữ liệu MST từ nguồn thuế'},
            status=404,
        )


# ─── NHÀ CUNG CẤP ────────────────────────────────────────────
@login_required
def ncc_list(request):
    q = request.GET.get('q', '').strip()
    trang_thai = request.GET.get('trang_thai', '1').strip()
    items = NhaCungCap.objects.filter(trang_thai=True)
    if trang_thai in ('0', '1'):
        items = NhaCungCap.objects.filter(trang_thai=(trang_thai == '1'))
    if q:
        items = items.filter(Q(ma_ncc__icontains=q) | Q(ten_ncc__icontains=q) |
                             Q(so_dien_thoai__icontains=q))
    page_obj = _paginate_queryset(request, items.order_by('-id'))
    return render(request, 'danh_muc/ncc_list.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'q': q,
        'trang_thai': trang_thai,
        'page_title': 'Nhà cung cấp', 'active_menu': 'nha_cung_cap',
    })


@login_required
def ncc_form(request, pk=None):
    obj = get_object_or_404(NhaCungCap, pk=pk) if pk else None
    if request.method == 'POST':
        data = request.POST
        if not obj:
            obj = NhaCungCap()
        ma_ncc = data.get('ma_ncc', '').strip().upper()
        ten_ncc = data.get('ten_ncc', '').strip()
        so_dien_thoai = data.get('so_dien_thoai', '').strip()

        if not ma_ncc or not ten_ncc or not so_dien_thoai:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin bắt buộc')
            return render(request, 'danh_muc/ncc_form.html', {
                'obj': obj,
                'page_title': 'Thêm NCC' if not pk else 'Sửa NCC',
                'active_menu': 'nha_cung_cap',
            })

        if so_dien_thoai and not _is_valid_phone(so_dien_thoai):
            messages.error(request, 'Số điện thoại không đúng định dạng')
            return render(request, 'danh_muc/ncc_form.html', {
                'obj': obj,
                'page_title': 'Thêm NCC' if not pk else 'Sửa NCC',
                'active_menu': 'nha_cung_cap',
            })

        if not pk and NhaCungCap.objects.filter(ma_ncc=ma_ncc).exists():
            messages.error(request, 'Mã nhà cung cấp đã tồn tại')
            return render(request, 'danh_muc/ncc_form.html', {
                'obj': obj,
                'page_title': 'Thêm NCC' if not pk else 'Sửa NCC',
                'active_menu': 'nha_cung_cap',
            })

        obj.ma_ncc = ma_ncc
        obj.ten_ncc = ten_ncc
        obj.loai_ncc = data.get('loai_ncc', 'dai_ly')
        obj.ma_so_thue = data.get('ma_so_thue', '')
        obj.dia_chi = data.get('dia_chi', '')
        obj.so_dien_thoai = so_dien_thoai
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


# ─── DANH MỤC HÀNG HÓA ───────────────────────────────────────
@login_required
def hang_hoa_list(request):
    q = request.GET.get('q', '').strip()
    nhom = request.GET.get('nhom', '').strip()
    items = HangHoa.objects.select_related('nhom_hang', 'thuong_hieu', 'don_vi_tinh').filter(trang_thai='dang_ban')
    if q:
        items = items.filter(
            Q(ma_hang__icontains=q) | Q(ten_hang__icontains=q) | Q(xe_tuong_thich__icontains=q)
        )
    if nhom:
        items = items.filter(nhom_hang_id=nhom)

    from apps.kho.models import TonKho

    page_obj = _paginate_queryset(request, items.order_by('-id'))

    hang_list = []
    for h in page_obj:
        ton = TonKho.objects.filter(hang_hoa=h).aggregate(t=Sum('so_luong'))['t'] or 0
        hang_list.append({'hang': h, 'ton': ton})

    return render(request, 'core/hang_hoa_list.html', {
        'hang_list': hang_list,
        'page_obj': page_obj,
        'nhom_list': NhomHang.objects.all(),
        'q': q,
        'nhom_filter': nhom,
        'page_title': 'Danh mục hàng hóa',
        'active_menu': 'hang_hoa',
    })


@login_required
def hang_hoa_form(request, pk=None):

    # Xử lý copy_from: nếu có tham số copy_from trên URL, lấy dữ liệu hàng hóa gốc để đổ vào form tạo mới
    copy_from = request.GET.get('copy_from')
    if pk:
        hang = get_object_or_404(HangHoa, pk=pk)
    elif copy_from:
        hang_copy = get_object_or_404(HangHoa, pk=copy_from)
        hang = HangHoa(
            ma_hang=_generate_next_ma_hang(),
            ten_hang=hang_copy.ten_hang,
            nhom_hang=hang_copy.nhom_hang,
            thuong_hieu=hang_copy.thuong_hieu,
            don_vi_tinh=hang_copy.don_vi_tinh,
            nha_cung_cap=hang_copy.nha_cung_cap,
            xe_tuong_thich=hang_copy.xe_tuong_thich,
            ton_toi_thieu=hang_copy.ton_toi_thieu,
            ton_toi_da=hang_copy.ton_toi_da,
            trang_thai='dang_ban',
            ghi_chu=hang_copy.ghi_chu,
        )
        so_vi_tri_default, _ = _extract_slot_size_and_note(hang.ghi_chu)
    else:
        hang = None
        if request.method != 'POST':
            hang = HangHoa(ma_hang=_generate_next_ma_hang())
    nhom_list = NhomHang.objects.all()
    thuong_hieu_list = ThuongHieu.objects.all()
    dvt_list = DonViTinh.objects.all()
    ncc_list = NhaCungCap.objects.filter(trang_thai=True).order_by('ma_ncc')
    so_vi_tri_default = 1
    if hang:
        so_vi_tri_default, _ = _extract_slot_size_and_note(hang.ghi_chu)

    def _render_hang_form(hang_obj):
        return render(request, 'core/hang_hoa_form.html', {
            'hang': hang_obj,
            'nhom_list': nhom_list,
            'thuong_hieu_list': thuong_hieu_list,
            'dvt_list': dvt_list,
            'ncc_list': ncc_list,
            'so_vi_tri_default': so_vi_tri_default,
            'page_title': 'Thêm hàng hóa' if not pk else 'Sửa hàng hóa',
            'active_menu': 'hang_hoa',
        })

    if request.method == 'POST':
        data = request.POST
        if not hang:
            hang = HangHoa()
        ma_hang = data.get('ma_hang', '').strip().upper()
        ten_hang = data.get('ten_hang', '').strip()
        nhom_hang_id = data.get('nhom_hang') or None
        don_vi_tinh_id = data.get('don_vi_tinh') or None
        try:
            so_vi_tri_default = int(data.get('so_vi_tri', 1) or 1)
        except ValueError:
            so_vi_tri_default = 1

        if so_vi_tri_default < 1 or so_vi_tri_default > 5:
            messages.error(request, 'Số vị trí chiếm dụng phải từ 1 đến 5')
            return _render_hang_form(hang)

        if not ten_hang or not don_vi_tinh_id:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin bắt buộc')
            return _render_hang_form(hang)

        if not ma_hang:
            ma_hang = _generate_next_ma_hang()

        if not pk and HangHoa.objects.filter(ma_hang=ma_hang).exists():
            messages.error(request, 'Mã hàng đã tồn tại')
            return _render_hang_form(hang)

        hang.ma_hang = ma_hang
        hang.ten_hang = ten_hang
        hang.nhom_hang_id = nhom_hang_id
        hang.thuong_hieu_id = data.get('thuong_hieu') or None
        hang.don_vi_tinh_id = don_vi_tinh_id
        hang.nha_cung_cap_id = data.get('nha_cung_cap') or None
        hang.xe_tuong_thich = data.get('xe_tuong_thich', '')
        hang.ton_toi_thieu = data.get('ton_toi_thieu', 0) or 0
        hang.ton_toi_da = data.get('ton_toi_da', 0) or 0
        hang.trang_thai = data.get('trang_thai', 'dang_ban')
        hang.ghi_chu = _merge_slot_size_and_note(so_vi_tri_default, data.get('ghi_chu', ''))
        try:
            hang.save()
            messages.success(request, f'Đã lưu hàng hóa: {hang.ten_hang}')
            return redirect('hang_hoa_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')

    if hang:
        _, clean_note = _extract_slot_size_and_note(hang.ghi_chu)
        hang.ghi_chu = clean_note

    return _render_hang_form(hang)


@login_required
def hang_hoa_xoa(request, pk):
    hang = get_object_or_404(HangHoa, pk=pk)
    if request.method == 'POST':
        ma_hang = hang.ma_hang
        ten_hang = hang.ten_hang
        try:
            hang.delete()
            messages.success(request, f'Đã xóa hàng hóa: {ma_hang} - {ten_hang}')
        except ProtectedError:
            messages.error(request, f'Không thể xóa {ma_hang} vì đang phát sinh chứng từ/tồn kho liên quan.')
    return redirect('hang_hoa_list')


@login_required
def hang_hoa_xoa_nhieu(request):
    if request.method != 'POST':
        return redirect('hang_hoa_list')

    ids = [int(x) for x in request.POST.getlist('ids[]') if str(x).isdigit()]
    if not ids:
        messages.error(request, 'Vui lòng chọn ít nhất 1 hàng hóa để xóa.')
        return redirect('hang_hoa_list')

    items = list(HangHoa.objects.filter(pk__in=ids))
    deleted = 0
    blocked_codes = []
    for item in items:
        try:
            item.delete()
            deleted += 1
        except ProtectedError:
            blocked_codes.append(item.ma_hang)

    if deleted:
        messages.success(request, f'Đã xóa {deleted} hàng hóa.')

    if blocked_codes:
        preview = ', '.join(blocked_codes[:5])
        suffix = '...' if len(blocked_codes) > 5 else ''
        messages.error(request, f'Không thể xóa {len(blocked_codes)} mã do có dữ liệu liên quan: {preview}{suffix}')

    if not deleted and not blocked_codes:
        messages.error(request, 'Không có hàng hóa hợp lệ để xóa.')

    return redirect('hang_hoa_list')


@login_required
def hang_hoa_api(request):
    ma = request.GET.get('ma', '').strip()
    hang_id = request.GET.get('hang_id', '').strip()
    from apps.kho.models import TonKho

    try:
        if hang_id:
            h = HangHoa.objects.get(pk=hang_id)
        else:
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
            'id': h.id,
            'ma_hang': h.ma_hang,
            'ten_hang': h.ten_hang,
            'dvt': h.don_vi_tinh.ten if h.don_vi_tinh else '',
            'ton_kho': ton,
            'gia_von': gia_von,
        })
    except HangHoa.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy'}, status=404)


@login_required
def hang_hoa_lookup_api(request):
    """Tra cứu hàng hóa theo mã/tên để dùng trong popup lọc."""
    q = request.GET.get('q', '').strip()
    only_available = str(request.GET.get('only_available', '')).strip().lower() in ('1', 'true', 'yes', 'on')
    kho_id = request.GET.get('kho_id')
    nhom_id = request.GET.get('nhom_id')
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 5))
    except ValueError:
        page_size = 5
    page_size = min(max(page_size, 1), 50)

    items = HangHoa.objects.select_related('don_vi_tinh').filter(trang_thai='dang_ban')
    if nhom_id:
        items = items.filter(nhom_hang_id=nhom_id)
    if q:
        items = items.filter(
            Q(ma_hang__icontains=q) |
            Q(ten_hang__icontains=q) |
            Q(ghi_chu__icontains=q)
        )

    if only_available:
        from apps.kho.models import TonKho

        ton_qs = TonKho.objects.filter(so_luong__gte=1)
        if kho_id:
            ton_qs = ton_qs.filter(kho_id=kho_id)
        available_ids = ton_qs.values_list('hang_hoa_id', flat=True).distinct()
        items = items.filter(pk__in=available_ids)

    items = items.order_by('ma_hang')
    total = items.count()
    total_pages = (total + page_size - 1) // page_size if total else 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    data = [
        {
            'id': h.id,
            'ma_hang': h.ma_hang,
            'ten_hang': h.ten_hang,
            'dvt': h.don_vi_tinh.ten if h.don_vi_tinh else '',
        }
        for h in page_items
    ]

    return JsonResponse({
        'results': data,
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
    })

@login_required
def kho_list(request):
    page_obj = _paginate_queryset(request, Kho.objects.filter(trang_thai=True).order_by('ma_kho'))
    return render(request, 'core/kho_list.html', {
        'kho_list': page_obj,
        'page_obj': page_obj,
        'page_title': 'Danh sách kho',
        'active_menu': 'kho',
    })


@login_required
def nhom_hang_list(request):
    q = request.GET.get('q', '').strip()
    if request.method == 'POST':
        action = (request.POST.get('action') or 'create').strip()
        if action == 'create':
            ma = request.POST.get('ma_nhom', '').strip().upper()
            ten = request.POST.get('ten_nhom', '').strip()
            mo_ta = request.POST.get('mo_ta', '').strip()
            bien_do = _parse_decimal_field(request.POST.get('bien_do_loi_nhuan', 10), 10)
            hang_ids = [x for x in request.POST.getlist('hang_ids[]') if str(x).isdigit()]
            if not ma:
                ma = _generate_next_ma_nhom()
            if not ten:
                messages.error(request, 'Vui lòng nhập tên nhóm')
            elif NhomHang.objects.filter(ma_nhom=ma).exists():
                messages.error(request, 'Mã nhóm đã tồn tại')
            else:
                nhom = NhomHang.objects.create(ma_nhom=ma, ten_nhom=ten, mo_ta=mo_ta, bien_do_loi_nhuan=bien_do)
                if hang_ids:
                    HangHoa.objects.filter(pk__in=hang_ids).update(nhom_hang=nhom)
                messages.success(request, 'Đã thêm nhóm hàng')
        elif action == 'update':
            nhom_id = request.POST.get('nhom_id')
            if not str(nhom_id).isdigit():
                messages.error(request, 'Nhóm hàng không hợp lệ')
            else:
                nhom = get_object_or_404(NhomHang, pk=nhom_id)
                ma = request.POST.get('ma_nhom', '').strip()
                ten = request.POST.get('ten_nhom', '').strip()
                mo_ta = request.POST.get('mo_ta', '').strip()
                bien_do = _parse_decimal_field(request.POST.get('bien_do_loi_nhuan', 10), 10)
                hang_ids = [int(x) for x in request.POST.getlist('hang_ids[]') if str(x).isdigit()]
                if not ma or not ten:
                    messages.error(request, 'Vui lòng nhập đủ mã nhóm và tên nhóm')
                elif NhomHang.objects.exclude(pk=nhom.pk).filter(ma_nhom=ma).exists():
                    messages.error(request, 'Mã nhóm đã tồn tại')
                else:
                    nhom.ma_nhom = ma
                    nhom.ten_nhom = ten
                    nhom.mo_ta = mo_ta
                    nhom.bien_do_loi_nhuan = bien_do
                    nhom.save(update_fields=['ma_nhom', 'ten_nhom', 'mo_ta', 'bien_do_loi_nhuan'])
                    HangHoa.objects.filter(nhom_hang=nhom).exclude(pk__in=hang_ids).update(nhom_hang=None)
                    if hang_ids:
                        HangHoa.objects.filter(pk__in=hang_ids).update(nhom_hang=nhom)
                    messages.success(request, 'Đã cập nhật nhóm hàng')
        elif action == 'delete':
            ids = [int(x) for x in request.POST.getlist('ids[]') if str(x).isdigit()]
            if not ids:
                messages.error(request, 'Vui lòng chọn nhóm hàng để xóa')
            else:
                qs = NhomHang.objects.filter(pk__in=ids)
                so_nhom = qs.count()
                try:
                    with transaction.atomic():
                        HangHoa.objects.filter(nhom_hang__in=qs).update(nhom_hang=None)
                        qs.delete()
                    messages.success(request, f'Đã xóa {so_nhom} nhóm hàng')
                except ProtectedError as exc:
                    messages.error(request, _build_protected_error_message(
                        exc,
                        'Không thể xóa nhóm hàng do còn chứng từ đang tham chiếu',
                    ))
        return redirect('nhom_hang_list')

    items = NhomHang.objects.order_by('ten_nhom')
    if q:
        items = items.filter(Q(ma_nhom__icontains=q) | Q(ten_nhom__icontains=q))
    items = _paginate_queryset(request, items)

    nhom_ids = [x.pk for x in items]
    nhom_meta = {nid: {'count': 0, 'hang_ids': [], 'hang_details': []} for nid in nhom_ids}
    for hh in HangHoa.objects.filter(nhom_hang_id__in=nhom_ids).values('pk', 'nhom_hang_id', 'ma_hang', 'ten_hang'):
        data = nhom_meta.get(hh['nhom_hang_id'])
        if data is not None:
            data['count'] += 1
            data['hang_ids'].append(str(hh['pk']))
            data['hang_details'].append({
                'id': hh['pk'],
                'ma': hh['ma_hang'],
                'ten': hh['ten_hang']
            })
    for item in items:
        meta = nhom_meta.get(item.pk, {'count': 0, 'hang_ids': [], 'hang_details': []})
        item.so_hang = meta['count']
        item.hang_ids_csv = ','.join(meta['hang_ids'])
        item.hang_details_json = json.dumps(meta['hang_details'])

    return render(request, 'core/nhom_hang.html', {
        'items': items,
        'page_obj': items,
        'q': q,
        'nhom_next_ma': _generate_next_ma_nhom(),
        'nhom_meta': nhom_meta,
        'page_title': 'Nhóm hàng',
        'active_menu': 'nhom_hang',
    })


@login_required
def don_vi_tinh_list(request):
    q = request.GET.get('q', '').strip()
    ten = ''

    if request.method == 'POST':
        ten = request.POST.get('ten', '').strip()
        if ten:
            if DonViTinh.objects.filter(ten__iexact=ten).exists():
                messages.error(request, 'Đơn vị tính đã tồn tại')
            else:
                DonViTinh.objects.create(ten=ten)
                messages.success(request, 'Đã thêm đơn vị tính')

    items = DonViTinh.objects.all()
    if q:
        items = items.filter(ten__icontains=q)

    page_obj = _paginate_queryset(request, items.order_by('ten'))
    return render(request, 'core/don_vi_tinh.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'q': q,
        'ten_default': ten,
        'page_title': 'Đơn vị tính',
        'active_menu': 'don_vi_tinh',
    })


@login_required
def vi_tri_kho_list(request):
    q = request.GET.get('q', '').strip()
    kho_id = request.GET.get('kho_id', '').strip()
    ma_pattern = re.compile(r'^(?P<side>[A-Z0-9]+)-D(?P<day>\d+)-K(?P<ke>\d+)-T(?P<tang>\d+)$')

    items = ViTriKho.objects.select_related('kho').all().order_by('kho__ma_kho', 'ma_vi_tri')
    if q:
        items = items.filter(
            Q(ma_vi_tri__icontains=q)
            | Q(mo_ta__icontains=q)
            | Q(kho__ma_kho__icontains=q)
            | Q(kho__ten_kho__icontains=q)
        )
    if kho_id:
        items = items.filter(kho_id=kho_id)

    page_obj = _paginate_queryset(request, items)
    items_display = []
    for item in page_obj:
        m = ma_pattern.match((item.ma_vi_tri or '').upper())
        items_display.append({
            'obj': item,
            'side': m.group('side') if m else '-',
            'day': int(m.group('day')) if m else None,
            'ke': int(m.group('ke')) if m else None,
            'tang': int(m.group('tang')) if m else None,
        })

    return render(request, 'core/vi_tri_kho_list.html', {
        'items': page_obj,
        'items_display': items_display,
        'page_obj': page_obj,
        'kho_list': Kho.objects.filter(trang_thai=True).order_by('ma_kho'),
        'q': q,
        'kho_id': kho_id,
        'page_title': 'Danh mục vị trí kho',
        'active_menu': 'vi_tri_kho',
    })


@login_required
def tai_khoan_ke_toan_list(request):
    q = request.GET.get('q', '').strip()
    if request.method == 'POST':
        ma_tk = request.POST.get('ma_tk', '').strip()
        ten_tk = request.POST.get('ten_tk', '').strip()
        tk_me_id = request.POST.get('tk_me') or None
        if ma_tk and ten_tk:
            if len(ma_tk) < 3:
                messages.error(request, 'Mã tài khoản phải có ít nhất 3 ký tự số')
            elif TaiKhoanKeToan.objects.filter(ma_tk=ma_tk).exists():
                messages.error(request, 'Mã tài khoản đã tồn tại')
            else:
                TaiKhoanKeToan.objects.create(ma_tk=ma_tk, ten_tk=ten_tk, tk_me_id=tk_me_id)
                messages.success(request, 'Đã thêm tài khoản kế toán')

    items = TaiKhoanKeToan.objects.select_related('tk_me')
    if q:
        items = items.filter(Q(ma_tk__icontains=q) | Q(ten_tk__icontains=q))
    items = items.order_by('ma_tk')
    return render(request, 'core/tai_khoan_ke_toan.html', {
        'items': items,
        'page_obj': None,
        'q': q,
        'tk_me_list': TaiKhoanKeToan.objects.filter(trang_thai=True).order_by('ma_tk'),
        'page_title': 'Danh mục tài khoản kế toán',
        'active_menu': 'tai_khoan_ke_toan',
    })


@login_required
def tai_khoan_api_lookup(request):
    """API endpoint để tìm kiếm tài khoản kế toán (AJAX)"""
    q = request.GET.get('q', '').strip()
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 5))
    except ValueError:
        page_size = 5
    page_size = min(max(page_size, 1), 50)

    items = (
        TaiKhoanKeToan.objects
        .filter(trang_thai=True)
        .annotate(ma_len=Length('ma_tk'))
        .filter(ma_len__gte=3)
        .order_by('ma_tk')
    )

    if q:
        items = items.filter(Q(ma_tk__icontains=q) | Q(ten_tk__icontains=q))

    total = items.count()
    total_pages = (total + page_size - 1) // page_size if total else 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    data = [
        {'ma_tk': tk.ma_tk, 'ten_tk': tk.ten_tk}
        for tk in page_items
    ]

    return JsonResponse({
        'results': data,
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
    })


@login_required
def nha_cung_cap_kh_api_lookup(request):
    """Tra cứu NCC lấy nguồn từ danh mục khách hàng có tích Nhà cung cấp."""
    q = request.GET.get('q', '').strip()
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 5))
    except ValueError:
        page_size = 5
    page_size = min(max(page_size, 1), 50)

    kh_qs = KhachHang.objects.filter(trang_thai=True, la_nha_cung_cap=True)
    if q:
        kh_qs = kh_qs.filter(
            Q(ma_kh__icontains=q) |
            Q(ten_kh__icontains=q) |
            Q(so_dien_thoai__icontains=q)
        )
    kh_qs = kh_qs.order_by('ma_kh')

    total = kh_qs.count()
    total_pages = (total + page_size - 1) // page_size if total else 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_rows = list(kh_qs[start:end])

    ma_kh_list = [r.ma_kh for r in page_rows]
    ncc_map = {
        n.ma_ncc: n.id
        for n in NhaCungCap.objects.filter(trang_thai=True, ma_ncc__in=ma_kh_list)
    }

    data = []
    for row in page_rows:
        ncc_id = ncc_map.get(row.ma_kh)
        if not ncc_id:
            continue
        data.append({
            'ncc_id': ncc_id,
            'ma_ncc': row.ma_kh,
            'ten_ncc': row.ten_kh,
            'so_dien_thoai': row.so_dien_thoai or '',
        })

    return JsonResponse({
        'results': data,
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
    })
@login_required
def vi_tri_kho_api_lookup(request):
    q = request.GET.get('q', '').strip()
    kho_id = request.GET.get('kho_id', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 5))
    
    from apps.kho.models import TonKhoViTri

    items = ViTriKho.objects.filter(trang_thai='hoat_dong')
    if kho_id:
        items = items.filter(kho_id=kho_id)
    if q:
        items = items.filter(ma_vi_tri__icontains=q)
    
    # Tính toán độ ưu tiên: Ô nào chưa có hàng (trống) sẽ được đẩy lên đầu
    # Lưu ý: Đây là xử lý memory-intensive nếu data quá lớn, nhưng với 100-200 ô kệ thì ổn.
    results_all = []
    for vt in items.order_by('ma_vi_tri'):
        da_dung = TonKhoViTri.objects.filter(vi_tri=vt).aggregate(s=Sum('so_luong'))['s'] or 0
        con_trong = (vt.suc_chua_toi_da or 50) - da_dung
        results_all.append({
            'id': vt.id,
            'ma_vi_tri': vt.ma_vi_tri,
            'da_dung': int(da_dung),
            'suc_chua': vt.suc_chua_toi_da or 50,
            'con_trong': int(con_trong),
            'is_empty': da_dung == 0
        })
    
    # Sắp xếp: Trống lên đầu
    results_all.sort(key=lambda x: x['is_empty'], reverse=True)
    
    paginator = Paginator(results_all, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'results': list(page_obj.object_list),
        'total': paginator.count,
        'page': page_obj.number,
        'total_pages': paginator.num_pages
    })
