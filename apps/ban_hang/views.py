"""Views cho app Bán Hàng"""
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.danh_muc.models import HangHoa, KhachHang, Kho, NhomHang

from .models import (DonBan, DonBan_CT, HoaDonBan, HoaDonBan_CT, PhieuGiaBan,
                     PhieuGiaBan_CT, PhieuGiaBanChietKhau, PhieuThu)

EXCEL_COMPANY_NAME = 'CÔNG TY PHẦN MỀM QUẢN LÝ DOANH NGHIỆP (ERP TIEN HUONG)'
EXCEL_COMPANY_ADDRESS = 'Tầng 3, Tòa nhà CT1B - Khu VOV, Mễ Trì, Nam Từ Liêm, Hà Nội'

HOA_DON_EXCEL_HEADERS = [
    ('Số hóa đơn', 'so_hoa_don'),
    ('Ngày lập', 'ngay_lap'),
    ('Ngày hạch toán', 'ngay_hach_toan'),
    ('Mã giao dịch', 'ma_giao_dich'),
    ('Mã khách', 'ma_kh'),
    ('Tên khách', 'ten_kh'),
    ('Địa chỉ', 'dia_chi'),
    ('SĐT', 'so_dien_thoai'),
    ('MST', 'mst'),
    ('Người mua hàng', 'nguoi_mua_hang'),
    ('Mã hàng', 'ma_hang'),
    ('Tên hàng', 'ten_hang'),
    ('Mã kho', 'ma_kho'),
    ('Tên kho', 'ten_kho'),
    ('Số lượng', 'so_luong'),
    ('Giá bán', 'gia_ban'),
    ('CK %', 'ty_le_chiet_khau'),
    ('Thuế %', 'thue_suat'),
    ('TK vật tư', 'tk_vat_tu'),
    ('TK giá vốn', 'tk_gia_von'),
    ('TK doanh thu', 'tk_doanh_thu'),
    ('Diễn giải', 'dien_giai'),
    ('Trạng thái', 'trang_thai'),
]


def _parse_decimal(value, default=Decimal('0')):
    if value in (None, ''):
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(',', '').strip())
    except (InvalidOperation, AttributeError):
        return default


def _parse_date(value, default=None):
    if value in (None, ''):
        return default or date.today()
    if hasattr(value, 'date') and callable(value.date):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                return date.fromisoformat(value) if fmt == '%Y-%m-%d' else timezone.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return default or date.today()


def _gen_so_hoa_don():
    now = timezone.now()
    return f'HD-{now.strftime("%Y%m%d-%H%M%S")}'


def _style_export_sheet(ws, title, headers):
    last_col = get_column_letter(len(headers))
    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'] = EXCEL_COMPANY_NAME
    ws['A1'].font = Font(name='Arial', size=12, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells(f'A2:{last_col}2')
    ws['A2'] = EXCEL_COMPANY_ADDRESS
    ws['A2'].font = Font(name='Arial', size=10)
    ws['A2'].alignment = Alignment(horizontal='center')

    ws.merge_cells(f'A4:{last_col}4')
    ws['A4'] = title
    ws['A4'].font = Font(name='Arial', size=16, bold=True)
    ws['A4'].alignment = Alignment(horizontal='center')

    header_fill = PatternFill('solid', fgColor='1F4E78')
    header_font = Font(color='FFFFFF', bold=True)
    for idx, (header, _) in enumerate(headers, start=1):
        cell = ws.cell(row=6, column=idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    ws.freeze_panes = 'A7'
    for idx, (header, _) in enumerate(headers, start=1):
        width = max(len(header) + 2, 12)
        if header in {'Tên khách', 'Địa chỉ', 'Diễn giải', 'Tên hàng', 'Tên kho'}:
            width = 24
        ws.column_dimensions[get_column_letter(idx)].width = width


def _find_header_row(ws, expected_headers):
    expected = [str(item).strip().lower() for item in expected_headers]
    for row in range(1, min(ws.max_row, 30) + 1):
        values = [str(ws.cell(row=row, column=col).value or '').strip().lower() for col in range(1, len(expected) + 1)]
        if values == expected:
            return row
    return None


def _hoa_don_ban_filtered_queryset(request):
    items = HoaDonBan.objects.select_related('khach_hang', 'don_ban', 'nguoi_tao')
    q = request.GET.get('q', '').strip()
    ma_giao_dich = request.GET.get('ma_giao_dich', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    ma_kh = request.GET.get('ma_kh', '').strip()

    if q:
        items = items.filter(
            Q(so_hoa_don__icontains=q)
            | Q(ten_kh__icontains=q)
            | Q(dia_chi__icontains=q)
            | Q(so_dien_thoai__icontains=q)
            | Q(mst__icontains=q)
            | Q(khach_hang__ma_kh__icontains=q)
            | Q(khach_hang__ten_kh__icontains=q)
        )
    if ma_giao_dich:
        items = items.filter(ma_giao_dich=ma_giao_dich)
    if trang_thai:
        items = items.filter(trang_thai=trang_thai)
    if tu_ngay:
        items = items.filter(ngay_lap__gte=tu_ngay)
    if den_ngay:
        items = items.filter(ngay_lap__lte=den_ngay)
    if ma_kh:
        items = items.filter(khach_hang__ma_kh__icontains=ma_kh)
    return items.order_by('-ngay_lap', '-id')


def _build_hoa_don_context(request, hoa_don=None):
    if hoa_don and hoa_don.khach_hang:
        kh_values = {
            'ten_kh': hoa_don.khach_hang.ten_kh,
            'so_dien_thoai': hoa_don.khach_hang.so_dien_thoai,
            'dia_chi': hoa_don.khach_hang.dia_chi,
            'mst': hoa_don.khach_hang.ma_so_thue,
        }
    else:
        kh_values = {'ten_kh': '', 'so_dien_thoai': '', 'dia_chi': '', 'mst': ''}

    return {
        'hoa_don': hoa_don,
        'editing': bool(hoa_don),
        'kh_list': KhachHang.objects.filter(trang_thai=True),
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban').select_related('don_vi_tinh'),
        'so_hoa_don_default': hoa_don.so_hoa_don if hoa_don else _gen_so_hoa_don(),
        'today': date.today(),
        **kh_values,
    }


def _save_hoa_don_from_request(request, hoa_don=None):
    data = request.POST
    kh_id = data.get('khach_hang') or None
    kh = KhachHang.objects.filter(pk=kh_id).first() if kh_id else None

    hoa_don = hoa_don or HoaDonBan()
    hoa_don.ma_giao_dich = data.get('ma_giao_dich', '1')
    hoa_don.so_hoa_don = data.get('so_hoa_don') or hoa_don.so_hoa_don or _gen_so_hoa_don()
    hoa_don.ngay_lap = _parse_date(data.get('ngay_lap'))
    hoa_don.ngay_hach_toan = _parse_date(data.get('ngay_hach_toan'))
    hoa_don.ma_ngoai_te = data.get('ma_ngoai_te', 'VND')
    hoa_don.ty_gia = _parse_decimal(data.get('ty_gia'), Decimal('1'))
    hoa_don.khach_hang = kh
    hoa_don.ten_kh = data.get('ten_kh') or (kh.ten_kh if kh else '')
    hoa_don.dia_chi = data.get('dia_chi') or (kh.dia_chi if kh else '')
    hoa_don.so_dien_thoai = data.get('so_dien_thoai') or (kh.so_dien_thoai if kh else '')
    hoa_don.mst = data.get('mst') or (kh.ma_so_thue if kh else '')
    hoa_don.nguoi_mua_hang = data.get('nguoi_mua_hang', '')
    hoa_don.tk_no = data.get('tk_no', '131')
    hoa_don.dien_giai = data.get('dien_giai', '')
    hoa_don.trang_thai = data.get('trang_thai', '1')
    if data.get('don_ban'):
        hoa_don.don_ban_id = data.get('don_ban')
    elif not hoa_don.pk:
        hoa_don.don_ban_id = None
    hoa_don.save()

    if hoa_don.pk:
        hoa_don.chi_tiet.all().delete()

    hang_ids = data.getlist('hang_id[]')
    kho_ids = data.getlist('kho_id[]')
    so_luongs = data.getlist('so_luong[]')
    gia_bans = data.getlist('gia_ban[]')
    ty_le_cks = data.getlist('ty_le_ck[]')
    thue_suats = data.getlist('thue_suat[]')

    valid_lines = 0
    for index in range(len(hang_ids)):
        hang_id = hang_ids[index] if index < len(hang_ids) else ''
        kho_id = kho_ids[index] if index < len(kho_ids) else ''
        if not hang_id or not kho_id:
            continue
        so_luong = _parse_decimal(so_luongs[index] if index < len(so_luongs) else 0)
        gia_ban = _parse_decimal(gia_bans[index] if index < len(gia_bans) else 0)
        if so_luong <= 0:
            continue

        HoaDonBan_CT.objects.create(
            hoa_don=hoa_don,
            hang_hoa_id=hang_id,
            kho_id=kho_id,
            so_luong=so_luong,
            gia_ban=gia_ban,
            ty_le_chiet_khau=_parse_decimal(ty_le_cks[index] if index < len(ty_le_cks) else 0),
            thue_suat=_parse_decimal(thue_suats[index] if index < len(thue_suats) else 10),
        )
        valid_lines += 1

    if valid_lines == 0:
        hoa_don.delete()
        raise ValueError('Hóa đơn phải có ít nhất 1 dòng hàng hóa hợp lệ')

    hoa_don.tinh_tong()
    return hoa_don


def _export_hoa_don_workbook(title, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = 'HoaDonBan'
    _style_export_sheet(ws, title, HOA_DON_EXCEL_HEADERS)

    for row_index, row in enumerate(rows, start=7):
        for col_index, (_, field_name) in enumerate(HOA_DON_EXCEL_HEADERS, start=1):
            value = row.get(field_name, '')
            cell = ws.cell(row=row_index, column=col_index, value=value)
            if field_name in {'ngay_lap', 'ngay_hach_toan'} and hasattr(value, 'strftime'):
                cell.value = value.strftime('%d/%m/%Y')
            if field_name in {'so_luong', 'gia_ban', 'ty_le_chiet_khau', 'thue_suat', 'tong_cong'}:
                cell.alignment = Alignment(horizontal='right')
    return wb


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


def don_ban_sua(request, pk):
    return _view_not_ready('sửa đơn bán hàng')


def don_ban_xoa(request, pk):
    return _view_not_ready('xóa đơn bán hàng')


def don_ban_chuyen_so_cai(request, pk):
    return _view_not_ready('chuyển sổ cái đơn bán hàng')


@login_required
def don_ban_export_data(request):
    rows = []
    items = DonBan.objects.select_related('khach_hang', 'kho', 'nhan_vien_ban')
    q = request.GET.get('q', '').strip()
    if q:
        items = items.filter(Q(so_don__icontains=q) | Q(ten_kh__icontains=q) | Q(sdt_kh__icontains=q))
    
    for don in items.prefetch_related('chi_tiet__hang_hoa'):
        for ct in don.chi_tiet.all():
            rows.append({
                'so_don': don.so_don,
                'ngay_ban': don.ngay_ban,
                'ma_kh': don.khach_hang.ma_kh if don.khach_hang else '',
                'ten_kh': don.ten_kh,
                'sdt_kh': don.sdt_kh,
                'ma_hang': ct.hang_hoa.ma_hang,
                'ten_hang': ct.hang_hoa.ten_hang,
                'so_luong': ct.so_luong,
                'don_gia': ct.don_gia,
                'chiet_khau': ct.chiet_khau,
                'thue_vat': ct.thue_vat,
                'trang_thai': don.get_trang_thai_display(),
            })
    
    wb = Workbook()
    ws = wb.active
    ws.title = 'DonBan'
    headers = [
        ('Số đơn', 'so_don'),
        ('Ngày bán', 'ngay_ban'),
        ('Mã khách', 'ma_kh'),
        ('Tên khách', 'ten_kh'),
        ('SĐT', 'sdt_kh'),
        ('Mã hàng', 'ma_hang'),
        ('Tên hàng', 'ten_hang'),
        ('Số lượng', 'so_luong'),
        ('Đơn giá', 'don_gia'),
        ('Chiết khấu', 'chiet_khau'),
        ('Thuế VAT', 'thue_vat'),
        ('Trạng thái', 'trang_thai'),
    ]
    _style_export_sheet(ws, 'DANH SÁCH ĐƠN BÁN HÀNG', headers)
    
    for row_index, row in enumerate(rows, start=7):
        for col_index, (_, field_name) in enumerate(headers, start=1):
            value = row.get(field_name, '')
            cell = ws.cell(row=row_index, column=col_index, value=value)
            if field_name == 'ngay_ban' and hasattr(value, 'strftime'):
                cell.value = value.strftime('%d/%m/%Y')
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=don_ban.xlsx'
    wb.save(response)
    return response


@login_required
def don_ban_export_template(request):
    wb = Workbook()
    ws = wb.active
    ws.title = 'DonBan'
    headers = [
        ('Số đơn', 'so_don'),
        ('Ngày bán', 'ngay_ban'),
        ('Mã khách', 'ma_kh'),
        ('Tên khách', 'ten_kh'),
        ('SĐT', 'sdt_kh'),
        ('Mã hàng', 'ma_hang'),
        ('Tên hàng', 'ten_hang'),
        ('Số lượng', 'so_luong'),
        ('Đơn giá', 'don_gia'),
        ('Chiết khấu', 'chiet_khau'),
        ('Thuế VAT', 'thue_vat'),
    ]
    _style_export_sheet(ws, 'MẪU NHẬP ĐƠN BÁN HÀNG', headers)
    ws['A7'] = 'Nhập dữ liệu từ dòng 7 trở đi, giữ nguyên các cột đã có.'
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=mau_don_ban.xlsx'
    wb.save(response)
    return response


@login_required
def don_ban_import_excel(request):
    if request.method != 'POST':
        return redirect('don_ban_list')
    
    uploaded = request.FILES.get('excel_file')
    if not uploaded:
        messages.error(request, 'Vui lòng chọn tệp Excel.')
        return redirect('don_ban_list')
    
    try:
        wb = load_workbook(uploaded)
    except Exception:
        messages.error(request, 'Không đọc được tệp Excel.')
        return redirect('don_ban_list')
    
    ws = wb.active
    created = updated = skipped = 0
    
    for row_idx in range(8, ws.max_row + 1):
        so_don = str(ws.cell(row=row_idx, column=1).value or '').strip()
        ngay_ban = ws.cell(row=row_idx, column=2).value
        ma_kh = str(ws.cell(row=row_idx, column=3).value or '').strip()
        ten_kh = str(ws.cell(row=row_idx, column=4).value or '').strip()
        sdt_kh = str(ws.cell(row=row_idx, column=5).value or '').strip()
        ma_hang = str(ws.cell(row=row_idx, column=6).value or '').strip()
        so_luong = ws.cell(row=row_idx, column=8).value
        don_gia = ws.cell(row=row_idx, column=9).value
        
        if not so_don or not ma_hang:
            skipped += 1
            continue
        
        kh = KhachHang.objects.filter(ma_kh=ma_kh).first() if ma_kh else None
        hang = HangHoa.objects.filter(ma_hang=ma_hang).first()
        
        if not hang:
            skipped += 1
            continue
        
        don = DonBan.objects.filter(so_don=so_don).first()
        if don:
            updated += 1
            don.chi_tiet.all().delete()
        else:
            don = DonBan()
            created += 1
        
        don.so_don = so_don
        don.ngay_ban = _parse_date(ngay_ban) if ngay_ban else date.today()
        don.khach_hang = kh
        don.ten_kh = ten_kh or (kh.ten_kh if kh else 'Khách lẻ')
        don.sdt_kh = sdt_kh
        don.nhan_vien_ban = request.user
        don.save()
        
        if so_luong and don_gia:
            DonBan_CT.objects.create(
                don_ban=don,
                hang_hoa=hang,
                so_luong=int(_parse_decimal(so_luong, 0)),
                don_gia=_parse_decimal(don_gia),
                chiet_khau=_parse_decimal(ws.cell(row=row_idx, column=10).value or 0),
                thue_vat=_parse_decimal(ws.cell(row=row_idx, column=11).value or 10),
            )
        don.tinh_tong()
    
    messages.success(request, f'Đã nhập đơn bán: tạo mới {created}, cập nhật {updated}, bỏ qua {skipped}.')
    return redirect('don_ban_list')



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


def _view_not_ready(feature_name):
    return HttpResponse(f'Chức năng {feature_name} đang được khôi phục.', status=501)


def khach_hang_api_lookup(request):
    query = (request.GET.get('q') or request.GET.get('term') or '').strip()
    items = KhachHang.objects.filter(trang_thai=True)
    if query:
        items = items.filter(
            Q(ma_kh__icontains=query)
            | Q(ten_kh__icontains=query)
            | Q(so_dien_thoai__icontains=query)
            | Q(dia_chi__icontains=query)
        )
    data = [
        {
            'id': kh.pk,
            'text': f'{kh.ma_kh} - {kh.ten_kh}',
            'ma_kh': kh.ma_kh,
            'ten_kh': kh.ten_kh,
            'so_dien_thoai': kh.so_dien_thoai,
            'dia_chi': kh.dia_chi,
        }
        for kh in items[:20]
    ]
    return JsonResponse({'results': data})


def khach_hang_lookup(request):
    return khach_hang_api_lookup(request)


def don_ban_api_lookup(request):
    q = request.GET.get('q', '').strip()
    khach_hang_id = request.GET.get('khach_hang_id')
    hoa_don_id = request.GET.get('hoa_don_id')

    items = DonBan.objects.select_related('khach_hang').filter(trang_thai='2')
    if q:
        items = items.filter(
            Q(so_don__icontains=q)
            | Q(ten_kh__icontains=q)
            | Q(khach_hang__ma_kh__icontains=q)
            | Q(khach_hang__ten_kh__icontains=q)
        )
    if khach_hang_id:
        items = items.filter(khach_hang_id=khach_hang_id)
    if hoa_don_id:
        items = items.exclude(hoa_don_lien_ket__id=hoa_don_id)

    results = []
    for item in items[:20]:
        results.append({
            'id': item.pk,
            'so_don': item.so_don,
            'ngay_chung_tu': item.ngay_chung_tu.strftime('%d/%m/%Y') if item.ngay_chung_tu else '',
            'ma_kh': item.khach_hang.ma_kh if item.khach_hang else '',
            'ten_kh': item.ten_kh,
            'tong_thanh_toan': float(item.tong_thanh_toan or 0),
        })
    return JsonResponse({'results': results})


def don_ban_api_detail(request, pk):
    don = get_object_or_404(DonBan.objects.select_related('khach_hang', 'kho'), pk=pk)
    rows = []
    for ct in don.chi_tiet.select_related('hang_hoa', 'kho'):
        rows.append({
            'hang_hoa_id': ct.hang_hoa_id,
            'kho_id': ct.kho_id,
            'so_luong': float(ct.so_luong or 0),
            'gia_ban': float(ct.don_gia or 0),
            'ty_le_ck': float(ct.chiet_khau or 0),
            'thue_suat': float(ct.thue_vat or 10),
        })
    return JsonResponse({
        'id': don.pk,
        'so_don': don.so_don,
        'ma_kh': don.khach_hang.ma_kh if don.khach_hang else '',
        'ten_kh': don.ten_kh,
        'kho_id': don.kho_id,
        'rows': rows,
    })


def phieu_thu_xac_nhan(request, pk):
    phieu = get_object_or_404(PhieuThu, pk=pk)
    if request.method == 'POST':
        phieu.trang_thai = '2'
        phieu.save(update_fields=['trang_thai'])
        messages.success(request, f'Đã xác nhận phiếu thu {phieu.so_phieu}')
    return redirect('phieu_thu_list')


def phieu_thu_chuyen_so_cai(request, pk):
    phieu = get_object_or_404(PhieuThu, pk=pk)
    if request.method == 'POST':
        phieu.trang_thai = '3'
        phieu.save(update_fields=['trang_thai'])
        messages.success(request, f'Đã chuyển phiếu thu {phieu.so_phieu} sang sổ cái')
    return redirect('phieu_thu_list')


def hoa_don_ban_list(request):
    items = _hoa_don_ban_filtered_queryset(request)[:100]
    context = {
        'items': items,
        'q': request.GET.get('q', '').strip(),
        'ma_giao_dich_filter': request.GET.get('ma_giao_dich', '').strip(),
        'trang_thai_filter': request.GET.get('trang_thai', '').strip(),
        'tu_ngay': request.GET.get('tu_ngay', '').strip(),
        'den_ngay': request.GET.get('den_ngay', '').strip(),
        'so_hd_tu': request.GET.get('so_hd_tu', '').strip(),
        'so_hd_den': request.GET.get('so_hd_den', '').strip(),
        'ma_kh': request.GET.get('ma_kh', '').strip(),
        'ma_hang': request.GET.get('ma_hang', '').strip(),
        'tk_vat_tu': request.GET.get('tk_vat_tu', '').strip(),
        'tk_gia_von': request.GET.get('tk_gia_von', '').strip(),
        'tk_doanh_thu': request.GET.get('tk_doanh_thu', '').strip(),
        'page_title': 'Hóa đơn bán hàng',
        'active_menu': 'hoa_don_ban',
    }
    return render(request, 'ban_hang/hoa_don_ban_list.html', context)


def hoa_don_ban_them(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                hoa_don = _save_hoa_don_from_request(request)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('hoa_don_ban_them')

        messages.success(request, f'Đã tạo hóa đơn {hoa_don.so_hoa_don}')
        return redirect('hoa_don_ban_detail', pk=hoa_don.pk)

    return render(request, 'ban_hang/hoa_don_ban_form.html', _build_hoa_don_context(request))


def hoa_don_ban_export_data(request):
    rows = []
    for hoa_don in _hoa_don_ban_filtered_queryset(request).prefetch_related('chi_tiet__hang_hoa', 'chi_tiet__kho'):
        for ct in hoa_don.chi_tiet.all():
            rows.append({
                'so_hoa_don': hoa_don.so_hoa_don,
                'ngay_lap': hoa_don.ngay_lap,
                'ngay_hach_toan': hoa_don.ngay_hach_toan,
                'ma_giao_dich': hoa_don.get_ma_giao_dich_display(),
                'ma_kh': hoa_don.khach_hang.ma_kh if hoa_don.khach_hang else '',
                'ten_kh': hoa_don.ten_kh,
                'dia_chi': hoa_don.dia_chi,
                'so_dien_thoai': hoa_don.so_dien_thoai,
                'mst': hoa_don.mst,
                'nguoi_mua_hang': hoa_don.nguoi_mua_hang,
                'ma_hang': ct.hang_hoa.ma_hang,
                'ten_hang': ct.hang_hoa.ten_hang,
                'ma_kho': ct.kho.ma_kho,
                'ten_kho': ct.kho.ten_kho,
                'so_luong': ct.so_luong,
                'gia_ban': ct.gia_ban,
                'ty_le_chiet_khau': ct.ty_le_chiet_khau,
                'thue_suat': ct.thue_suat,
                'tk_vat_tu': ct.tk_vat_tu,
                'tk_gia_von': ct.tk_gia_von,
                'tk_doanh_thu': ct.tk_doanh_thu,
                'dien_giai': hoa_don.dien_giai,
                'trang_thai': hoa_don.get_trang_thai_display(),
            })

    wb = _export_hoa_don_workbook('DANH SÁCH HÓA ĐƠN BÁN HÀNG', rows)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=hoa_don_ban.xlsx'
    wb.save(response)
    return response


def hoa_don_ban_export_template(request):
    wb = _export_hoa_don_workbook('MẪU NHẬP HÓA ĐƠN BÁN HÀNG', [])
    ws = wb.active
    ws['A7'] = 'Nhập dữ liệu từ dòng 7 trở đi, giữ nguyên các cột đã có.'
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=mau_hoa_don_ban.xlsx'
    wb.save(response)
    return response


def hoa_don_ban_import_excel(request):
    if request.method != 'POST':
        return redirect('hoa_don_ban_list')

    uploaded = request.FILES.get('excel_file')
    if not uploaded:
        messages.error(request, 'Vui lòng chọn tệp Excel.')
        return redirect('hoa_don_ban_list')

    try:
        wb = load_workbook(uploaded)
    except Exception:
        messages.error(request, 'Không đọc được tệp Excel.')
        return redirect('hoa_don_ban_list')

    ws = wb.active
    header_row = _find_header_row(ws, [header for header, _ in HOA_DON_EXCEL_HEADERS])
    if not header_row:
        messages.error(request, 'Không tìm thấy dòng tiêu đề hợp lệ trong tệp Excel.')
        return redirect('hoa_don_ban_list')

    header_map = {}
    for col in range(1, ws.max_column + 1):
        value = str(ws.cell(row=header_row, column=col).value or '').strip()
        if value:
            header_map[value] = col

    required = ['Số hóa đơn', 'Mã khách', 'Mã hàng', 'Mã kho', 'Số lượng', 'Giá bán']
    missing = [label for label in required if label not in header_map]
    if missing:
        messages.error(request, f'Thiếu cột bắt buộc: {", ".join(missing)}')
        return redirect('hoa_don_ban_list')

    grouped_rows = {}
    for row in range(header_row + 1, ws.max_row + 1):
        so_hoa_don = str(ws.cell(row=row, column=header_map['Số hóa đơn']).value or '').strip()
        if not so_hoa_don:
            continue
        grouped_rows.setdefault(so_hoa_don, []).append(row)

    created = updated = skipped = 0
    with transaction.atomic():
        for so_hoa_don, row_numbers in grouped_rows.items():
            first_row = row_numbers[0]
            kh_code = str(ws.cell(row=first_row, column=header_map['Mã khách']).value or '').strip()
            kh = KhachHang.objects.filter(ma_kh=kh_code).first()
            if not kh:
                skipped += 1
                continue

            hoa_don = HoaDonBan.objects.filter(so_hoa_don=so_hoa_don).select_related('khach_hang').first()
            if hoa_don:
                updated += 1
                hoa_don.chi_tiet.all().delete()
            else:
                hoa_don = HoaDonBan(so_hoa_don=so_hoa_don)
                created += 1

            hoa_don.ma_giao_dich = str(ws.cell(row=first_row, column=header_map.get('Mã giao dịch', 0)).value or '1')[:5] if header_map.get('Mã giao dịch') else '1'
            hoa_don.ngay_lap = _parse_date(ws.cell(row=first_row, column=header_map.get('Ngày lập', 1)).value)
            hoa_don.ngay_hach_toan = _parse_date(ws.cell(row=first_row, column=header_map.get('Ngày hạch toán', 2)).value)
            hoa_don.ma_ngoai_te = 'VND'
            hoa_don.ty_gia = Decimal('1')
            hoa_don.khach_hang = kh
            hoa_don.ten_kh = str(ws.cell(row=first_row, column=header_map.get('Tên khách', 0)).value or kh.ten_kh)
            hoa_don.dia_chi = str(ws.cell(row=first_row, column=header_map.get('Địa chỉ', 0)).value or kh.dia_chi)
            hoa_don.so_dien_thoai = str(ws.cell(row=first_row, column=header_map.get('SĐT', 0)).value or kh.so_dien_thoai)
            hoa_don.mst = str(ws.cell(row=first_row, column=header_map.get('MST', 0)).value or kh.ma_so_thue)
            hoa_don.nguoi_mua_hang = str(ws.cell(row=first_row, column=header_map.get('Người mua hàng', 0)).value or '')
            hoa_don.tk_no = '131'
            hoa_don.dien_giai = str(ws.cell(row=first_row, column=header_map.get('Diễn giải', 0)).value or '')
            hoa_don.trang_thai = '1'
            hoa_don.save()

            for row in row_numbers:
                hang_code = str(ws.cell(row=row, column=header_map['Mã hàng']).value or '').strip()
                kho_code = str(ws.cell(row=row, column=header_map['Mã kho']).value or '').strip()
                hang = HangHoa.objects.filter(ma_hang=hang_code).first()
                kho = Kho.objects.filter(ma_kho=kho_code).first()
                if not hang or not kho:
                    continue
                HoaDonBan_CT.objects.create(
                    hoa_don=hoa_don,
                    hang_hoa=hang,
                    kho=kho,
                    so_luong=_parse_decimal(ws.cell(row=row, column=header_map['Số lượng']).value),
                    gia_ban=_parse_decimal(ws.cell(row=row, column=header_map['Giá bán']).value),
                    ty_le_chiet_khau=_parse_decimal(ws.cell(row=row, column=header_map.get('CK %', 0)).value if header_map.get('CK %') else 0),
                    thue_suat=_parse_decimal(ws.cell(row=row, column=header_map.get('Thuế %', 0)).value if header_map.get('Thuế %') else 10),
                    tk_vat_tu=str(ws.cell(row=row, column=header_map.get('TK vật tư', 0)).value or ''),
                    tk_gia_von=str(ws.cell(row=row, column=header_map.get('TK giá vốn', 0)).value or ''),
                    tk_doanh_thu=str(ws.cell(row=row, column=header_map.get('TK doanh thu', 0)).value or ''),
                )
            hoa_don.tinh_tong()

    messages.success(request, f'Đã nhập hóa đơn: tạo mới {created}, cập nhật {updated}, bỏ qua {skipped}.')
    return redirect('hoa_don_ban_list')


def hoa_don_ban_detail(request, pk):
    hoa_don = get_object_or_404(HoaDonBan.objects.select_related('khach_hang', 'don_ban'), pk=pk)
    chi_tiet = hoa_don.chi_tiet.select_related('hang_hoa', 'kho')
    return render(request, 'ban_hang/hoa_don_ban_detail.html', {
        'hoa_don': hoa_don,
        'chi_tiet': chi_tiet,
        'page_title': f'Hóa đơn {hoa_don.so_hoa_don}',
        'active_menu': 'hoa_don_ban',
    })


def hoa_don_ban_copy(request, pk):
    source = get_object_or_404(HoaDonBan.objects.select_related('khach_hang', 'don_ban'), pk=pk)
    with transaction.atomic():
        copy_hd = HoaDonBan.objects.create(
            ma_giao_dich=source.ma_giao_dich,
            so_hoa_don=_gen_so_hoa_don(),
            ngay_lap=date.today(),
            ngay_hach_toan=date.today(),
            ma_ngoai_te=source.ma_ngoai_te,
            ty_gia=source.ty_gia,
            khach_hang=source.khach_hang,
            ten_kh=source.ten_kh,
            dia_chi=source.dia_chi,
            so_dien_thoai=source.so_dien_thoai,
            mst=source.mst,
            nguoi_mua_hang=source.nguoi_mua_hang,
            tk_no=source.tk_no,
            dien_giai=source.dien_giai,
            trang_thai='1',
            don_ban=source.don_ban,
            nguoi_tao=request.user if request.user.is_authenticated else None,
        )
        for ct in source.chi_tiet.all():
            HoaDonBan_CT.objects.create(
                hoa_don=copy_hd,
                hang_hoa=ct.hang_hoa,
                kho=ct.kho,
                so_luong=ct.so_luong,
                gia_ban=ct.gia_ban,
                ty_le_chiet_khau=ct.ty_le_chiet_khau,
                thue_suat=ct.thue_suat,
                tk_vat_tu=ct.tk_vat_tu,
                tk_gia_von=ct.tk_gia_von,
                tk_doanh_thu=ct.tk_doanh_thu,
            )
        copy_hd.tinh_tong()
    messages.success(request, f'Đã sao chép hóa đơn thành {copy_hd.so_hoa_don}')
    return redirect('hoa_don_ban_detail', pk=copy_hd.pk)


def hoa_don_ban_sua(request, pk):
    hoa_don = get_object_or_404(HoaDonBan, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                _save_hoa_don_from_request(request, hoa_don)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('hoa_don_ban_sua', pk=pk)
        messages.success(request, f'Đã cập nhật hóa đơn {hoa_don.so_hoa_don}')
        return redirect('hoa_don_ban_detail', pk=hoa_don.pk)

    return render(request, 'ban_hang/hoa_don_ban_form.html', {
        **_build_hoa_don_context(request, hoa_don),
        'chi_tiet': hoa_don.chi_tiet.select_related('hang_hoa', 'kho'),
    })


def hoa_don_ban_xoa(request, pk):
    hoa_don = get_object_or_404(HoaDonBan, pk=pk)
    if request.method == 'POST':
        hoa_don.delete()
        messages.success(request, f'Đã xóa hóa đơn {hoa_don.so_hoa_don}')
    return redirect('hoa_don_ban_list')


def hoa_don_ban_chuyen_so_cai(request, pk):
    hoa_don = get_object_or_404(HoaDonBan, pk=pk)
    if request.method == 'POST':
        hoa_don.trang_thai = '3'
        hoa_don.save(update_fields=['trang_thai'])
        messages.success(request, f'Đã chuyển sổ cái hóa đơn {hoa_don.so_hoa_don}')
    return redirect('hoa_don_ban_detail', pk=pk)


def hoa_don_ban_in(request, pk):
    hoa_don = get_object_or_404(HoaDonBan.objects.select_related('khach_hang', 'don_ban'), pk=pk)
    chi_tiet = hoa_don.chi_tiet.select_related('hang_hoa', 'kho')
    if request.GET.get('format') == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = 'HoaDonBan'
        _style_export_sheet(ws, f'HÓA ĐƠN {hoa_don.so_hoa_don}', [
            ('STT', 'stt'),
            ('Mã hàng', 'ma_hang'),
            ('Tên hàng', 'ten_hang'),
            ('Kho', 'kho'),
            ('Số lượng', 'so_luong'),
            ('Giá bán', 'gia_ban'),
            ('CK %', 'ck'),
            ('Thuế %', 'thue'),
            ('Thành tiền', 'thanh_tien'),
        ])
        for index, ct in enumerate(chi_tiet, start=1):
            ws.cell(row=6 + index, column=1, value=index)
            ws.cell(row=6 + index, column=2, value=ct.hang_hoa.ma_hang)
            ws.cell(row=6 + index, column=3, value=ct.hang_hoa.ten_hang)
            ws.cell(row=6 + index, column=4, value=ct.kho.ma_kho)
            ws.cell(row=6 + index, column=5, value=float(ct.so_luong or 0))
            ws.cell(row=6 + index, column=6, value=float(ct.gia_ban or 0))
            ws.cell(row=6 + index, column=7, value=float(ct.ty_le_chiet_khau or 0))
            ws.cell(row=6 + index, column=8, value=float(ct.thue_suat or 0))
            ws.cell(row=6 + index, column=9, value=float(ct.thanh_tien or 0))
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={hoa_don.so_hoa_don}.xlsx'
        wb.save(response)
        return response

    return render(request, 'ban_hang/hoa_don_ban_print.html', {
        'hoa_don': hoa_don,
        'chi_tiet': chi_tiet,
        'page_title': f'In hóa đơn {hoa_don.so_hoa_don}',
        'active_menu': 'hoa_don_ban',
    })


def gia_ban_list(request):
    q = request.GET.get('q', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()

    items = PhieuGiaBan.objects.select_related('nhom_hang', 'nguoi_lap').prefetch_related('chi_tiet__hang_hoa__don_vi_tinh')
    if q:
        items = items.filter(
            Q(ma_phieu__icontains=q)
            | Q(nhom_hang__ma_nhom__icontains=q)
            | Q(nhom_hang__ten_nhom__icontains=q)
            | Q(chi_tiet__hang_hoa__ma_hang__icontains=q)
            | Q(chi_tiet__hang_hoa__ten_hang__icontains=q)
        ).distinct()
    if trang_thai:
        items = items.filter(trang_thai_duyet=trang_thai)

    rows = []
    for phieu in items.order_by('-ngay_lap', '-ngay_tao'):
        for ct in phieu.chi_tiet.all():
            rows.append({
                'phieu_id': phieu.pk,
                'phieu__trang_thai_duyet': phieu.trang_thai_duyet,
                'phieu__ma_phieu': phieu.ma_phieu,
                'phieu__ngay_hieu_luc': phieu.ngay_hieu_luc,
                'phieu__loai_tien_te': phieu.loai_tien_te,
                'hang_hoa__ma_hang': ct.hang_hoa.ma_hang,
                'hang_hoa__ten_hang': ct.hang_hoa.ten_hang,
                'hang_hoa__don_vi_tinh__ten': ct.hang_hoa.don_vi_tinh.ten if ct.hang_hoa.don_vi_tinh else '',
                'gia_ban_chuan': ct.gia_ban_chuan,
            })

    return render(request, 'ban_hang/gia_ban_list.html', {
        'rows': rows,
        'q': q,
        'trang_thai': trang_thai,
        'page_title': 'Quản lý giá bán',
        'active_menu': 'gia_ban',
    })


def gia_ban_them(request):
    return _gia_ban_form(request)


def _gen_ma_phieu_gia_ban():
    last = PhieuGiaBan.objects.order_by('-id').first()
    if not last:
        return 'GB1'
    digits = ''.join(ch for ch in last.ma_phieu if ch.isdigit())
    next_num = int(digits or 0) + 1
    return f'GB{next_num}'


def _gia_ban_validate_and_save(request, phieu=None):
    data = request.POST
    nhom_hang_id = data.get('nhom_hang')
    nhom_hang = NhomHang.objects.filter(pk=nhom_hang_id).first() if nhom_hang_id else None

    ma_phieu = data.get('ma_phieu') or _gen_ma_phieu_gia_ban()
    ngay_lap = _parse_date(data.get('ngay_lap'))
    ngay_hieu_luc = _parse_date(data.get('ngay_hieu_luc'))
    default_bien_do = nhom_hang.bien_do_loi_nhuan if nhom_hang else Decimal('10')
    bien_do_loi_nhuan = _parse_decimal(data.get('bien_do_loi_nhuan'), default_bien_do)
    loai_tien_te = data.get('loai_tien_te', 'VND')
    ghi_chu = data.get('ghi_chu', '')

    if phieu is None and PhieuGiaBan.objects.filter(ma_phieu=ma_phieu).exists():
        raise ValueError('Mã phiếu giá bán đã tồn tại')

    if phieu and phieu.trang_thai_duyet != 'cho_duyet':
        raise ValueError('Chỉ được sửa phiếu giá bán ở trạng thái chờ duyệt')

    hang_ids = data.getlist('hang_id[]')
    gia_vons = data.getlist('gia_von[]')
    gia_ban_chuans = data.getlist('gia_ban_chuan[]')
    ck_tu_list = data.getlist('ck_tu[]')
    ck_den_list = data.getlist('ck_den[]')
    ck_pt_list = data.getlist('ck_pt[]')

    detail_rows = []
    seen_hang = set()
    for idx, hang_id in enumerate(hang_ids):
        if not hang_id:
            continue
        hang = HangHoa.objects.select_related('don_vi_tinh', 'nhom_hang').filter(pk=hang_id).first()
        if not hang:
            raise ValueError('Vui lòng kiểm tra lại thông tin các trường dữ liệu bắt buộc')

        gia_von = _parse_decimal(gia_vons[idx] if idx < len(gia_vons) else 0)
        gia_ban_chuan = _parse_decimal(gia_ban_chuans[idx] if idx < len(gia_ban_chuans) else 0)

        if gia_von < 0 or gia_ban_chuan < 0:
            raise ValueError('Vui lòng kiểm tra lại thông tin các trường dữ liệu bắt buộc')
        if gia_ban_chuan < gia_von:
            raise ValueError('Giá bán mới không được nhỏ hơn giá vốn')
        if hang.pk in seen_hang:
            raise ValueError('Vui lòng kiểm tra lại thông tin các trường dữ liệu bắt buộc')
        seen_hang.add(hang.pk)

        detail_rows.append({
            'hang': hang,
            'gia_von': gia_von,
            'gia_ban_chuan': gia_ban_chuan,
        })

    if not detail_rows:
        raise ValueError('Vui lòng kiểm tra lại thông tin các trường dữ liệu bắt buộc')

    # Nhóm hàng không bắt buộc nhập tay: tự suy ra từ mặt hàng đầu tiên.
    if not nhom_hang:
        nhom_hang = detail_rows[0]['hang'].nhom_hang
    if not nhom_hang and phieu and phieu.nhom_hang_id:
        nhom_hang = phieu.nhom_hang
    if not nhom_hang:
        raise ValueError('Không xác định được nhóm hàng cho phiếu giá bán')

    discount_rows = []
    ranges = []
    for idx in range(max(len(ck_tu_list), len(ck_den_list), len(ck_pt_list))):
        tu = ck_tu_list[idx] if idx < len(ck_tu_list) else ''
        den = ck_den_list[idx] if idx < len(ck_den_list) else ''
        pt = ck_pt_list[idx] if idx < len(ck_pt_list) else ''
        if not tu and not den and not pt:
            continue
        tu_int = int(_parse_decimal(tu, 0))
        den_int = int(_parse_decimal(den, 0))
        pt_dec = _parse_decimal(pt, Decimal('0'))
        if tu_int <= 0 or den_int <= 0 or tu_int > den_int or pt_dec < 0:
            raise ValueError('Khoảng số lượng chiết khấu không hợp lệ')
        for used_tu, used_den in ranges:
            if not (den_int < used_tu or used_den < tu_int):
                raise ValueError('Khoảng số lượng chiết khấu không hợp lệ')
        ranges.append((tu_int, den_int))
        discount_rows.append({'tu': tu_int, 'den': den_int, 'pt': pt_dec})

    with transaction.atomic():
        phieu = phieu or PhieuGiaBan()
        phieu.ma_phieu = ma_phieu
        phieu.ngay_lap = ngay_lap
        phieu.ngay_hieu_luc = ngay_hieu_luc
        phieu.nguoi_lap = request.user
        phieu.nhom_hang = nhom_hang
        phieu.bien_do_loi_nhuan = bien_do_loi_nhuan
        phieu.loai_tien_te = loai_tien_te
        phieu.trang_thai_duyet = 'cho_duyet'
        phieu.ghi_chu = ghi_chu
        phieu.save()

        phieu.chi_tiet.all().delete()
        phieu.bang_chiet_khau.all().delete()

        for row in detail_rows:
            PhieuGiaBan_CT.objects.create(
                phieu=phieu,
                hang_hoa=row['hang'],
                gia_von=row['gia_von'],
                gia_ban_chuan=row['gia_ban_chuan'],
            )
        for row in discount_rows:
            PhieuGiaBanChietKhau.objects.create(
                phieu=phieu,
                tu_so_luong=row['tu'],
                den_so_luong=row['den'],
                phan_tram_chiet_khau=row['pt'],
            )

    return phieu


def _gia_ban_form(request, phieu=None):
    if request.method == 'POST':
        try:
            phieu = _gia_ban_validate_and_save(request, phieu)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect(request.path)

        messages.success(request, 'Thêm giá bán thành công' if request.path.endswith('/them/') else 'Cập nhật phiếu giá bán thành công')
        return redirect('gia_ban_list')

    context = {
        'phieu': phieu,
        'editing': bool(phieu),
        'nhom_list': NhomHang.objects.all().order_by('ten_nhom'),
        'hang_list': HangHoa.objects.select_related('don_vi_tinh', 'nhom_hang').order_by('ma_hang'),
        'ma_phieu_default': phieu.ma_phieu if phieu else _gen_ma_phieu_gia_ban(),
        'today': date.today(),
        'page_title': 'Sửa phiếu giá bán' if phieu else 'Thêm phiếu giá bán',
        'active_menu': 'gia_ban',
        'chi_tiet': phieu.chi_tiet.select_related('hang_hoa__don_vi_tinh') if phieu else [],
        'bang_ck': phieu.bang_chiet_khau.all() if phieu else [],
    }
    return render(request, 'ban_hang/gia_ban_form.html', context)


def gia_ban_export_template(request):
    return _view_not_ready('xuất mẫu bảng giá bán')


def gia_ban_import_excel(request):
    return _view_not_ready('nhập bảng giá bán từ Excel')


def gia_ban_copy(request, pk):
    source = get_object_or_404(PhieuGiaBan.objects.select_related('nhom_hang'), pk=pk)
    clone = PhieuGiaBan.objects.create(
        ma_phieu=_gen_ma_phieu_gia_ban(),
        ngay_lap=date.today(),
        ngay_hieu_luc=source.ngay_hieu_luc,
        nguoi_lap=request.user,
        nhom_hang=source.nhom_hang,
        bien_do_loi_nhuan=source.bien_do_loi_nhuan,
        loai_tien_te=source.loai_tien_te,
        trang_thai_duyet='cho_duyet',
        ghi_chu=source.ghi_chu,
    )
    for ct in source.chi_tiet.all():
        PhieuGiaBan_CT.objects.create(
            phieu=clone,
            hang_hoa=ct.hang_hoa,
            gia_von=ct.gia_von,
            gia_ban_chuan=ct.gia_ban_chuan,
        )
    for ck in source.bang_chiet_khau.all():
        PhieuGiaBanChietKhau.objects.create(
            phieu=clone,
            tu_so_luong=ck.tu_so_luong,
            den_so_luong=ck.den_so_luong,
            phan_tram_chiet_khau=ck.phan_tram_chiet_khau,
        )
    messages.success(request, f'Đã sao chép phiếu giá bán thành {clone.ma_phieu}')
    return redirect('gia_ban_sua', pk=clone.pk)


def gia_ban_sua(request, pk):
    phieu = get_object_or_404(PhieuGiaBan, pk=pk)
    return _gia_ban_form(request, phieu)


def gia_ban_xoa(request, pk):
    phieu = get_object_or_404(PhieuGiaBan, pk=pk)
    if phieu.trang_thai_duyet != 'cho_duyet':
        messages.error(request, 'Phiếu giá bán đã được duyệt, không được phép xóa')
        return redirect('gia_ban_list')
    if request.method == 'POST':
        phieu.delete()
        messages.success(request, 'Đã xóa phiếu giá bán')
    return redirect('gia_ban_list')


def gia_ban_hang_hoa_api(request):
    hang_id = request.GET.get('hang_id')
    hang = HangHoa.objects.select_related('don_vi_tinh', 'nhom_hang').filter(pk=hang_id).first()
    if not hang:
        return JsonResponse({'error': 'Không tìm thấy'}, status=404)

    gia_von = hang.get_gia_von() if hasattr(hang, 'get_gia_von') else 0
    bien_do = hang.nhom_hang.bien_do_loi_nhuan if hang.nhom_hang and hasattr(hang.nhom_hang, 'bien_do_loi_nhuan') else 0
    gia_ban_chuan = None

    phieu_gia = (
        PhieuGiaBan.objects
        .filter(trang_thai_duyet='da_duyet', ngay_hieu_luc__lte=date.today(), chi_tiet__hang_hoa=hang)
        .select_related('nhom_hang')
        .prefetch_related('chi_tiet')
        .order_by('-ngay_hieu_luc', '-ngay_cap_nhat', '-id')
        .first()
    )
    if phieu_gia:
        ct_gia = phieu_gia.chi_tiet.filter(hang_hoa=hang).first()
        if ct_gia:
            gia_ban_chuan = ct_gia.gia_ban_chuan

    if gia_ban_chuan is None:
        gia_ban_chuan = round(Decimal(gia_von or 0) * (Decimal('1') + Decimal(bien_do or 0) / Decimal('100')), 0)

    return JsonResponse({
        'id': hang.pk,
        'ma_hang': hang.ma_hang,
        'ten_hang': hang.ten_hang,
        'don_vi_tinh': hang.don_vi_tinh.ten if hang.don_vi_tinh else '',
        'nhom_hang_id': hang.nhom_hang_id,
        'bien_do_loi_nhuan': float(bien_do or 0),
        'gia_von': float(gia_von or 0),
        'gia_ban_chuan': float(gia_ban_chuan or 0),
        'gia_ban_nguon': 'phieu_gia_ban' if phieu_gia else 'bien_do_nhom',
    })
