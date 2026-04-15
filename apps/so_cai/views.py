from datetime import date
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.danh_muc.models import KhachHang, NhaCungCap, TaiKhoanKeToan
from apps.so_cai.models import KyKeToan
from apps.so_cai.periods import build_year_period_rows

from .services import (LedgerPostingError, get_general_ledger,
                       get_trial_balance, post_to_ledger)


def _parse_date(raw, default_value):
    if not raw:
        return default_value
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return default_value


@login_required
def ky_ke_toan_view(request):
    today = date.today()
    year_raw = request.GET.get('nam') or request.POST.get('nam') or today.year
    try:
        year = int(year_raw)
    except (TypeError, ValueError):
        year = today.year

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        if action == 'generate':
            try:
                with transaction.atomic():
                    created = KyKeToan.tao_12_ky_cho_nam(year, nguoi_tao=request.user)
                messages.success(request, f'Đã khởi tạo {len(created)} kỳ kế toán cho năm {year}.')
            except (OperationalError, ProgrammingError):
                messages.warning(request, 'Bảng kỳ kế toán chưa sẵn sàng trên CSDL. Trang vẫn hiển thị tạm, nhưng bạn cần apply migration để tạo/lưu kỳ.')
            return redirect(f'{request.path}?nam={year}')

        if action == 'set_current':
            try:
                ky = get_object_or_404(KyKeToan, pk=request.POST.get('ky_id'))
                with transaction.atomic():
                    KyKeToan.dat_ky_hien_tai(ky.id)
                messages.success(request, f'Đã chọn {ky} làm kỳ đang sử dụng.')
                return redirect(f'{request.path}?nam={ky.nam}')
            except (OperationalError, ProgrammingError):
                messages.warning(request, 'Bảng kỳ kế toán chưa có trên CSDL nên chưa thể chọn kỳ đang sử dụng.')
                return redirect(f'{request.path}?nam={year}')

        if action in {'lock', 'unlock'}:
            try:
                ky = get_object_or_404(KyKeToan, pk=request.POST.get('ky_id'))
                if action == 'lock':
                    ky.trang_thai = 'locked'
                    ky.khoa_luc = timezone.now()
                    ky.khoa_boi = request.user
                    ky.save(update_fields=['trang_thai', 'khoa_luc', 'khoa_boi', 'ngay_cap_nhat'])
                    messages.success(request, f'Đã khóa {ky}.')
                else:
                    ky.trang_thai = 'open'
                    ky.khoa_luc = None
                    ky.khoa_boi = None
                    ky.save(update_fields=['trang_thai', 'khoa_luc', 'khoa_boi', 'ngay_cap_nhat'])
                    messages.success(request, f'Đã mở {ky}.')
                return redirect(f'{request.path}?nam={ky.nam}')
            except (OperationalError, ProgrammingError):
                messages.warning(request, 'Bảng kỳ kế toán chưa có trên CSDL nên chưa thể khóa/mở kỳ.')
                return redirect(f'{request.path}?nam={year}')

    try:
        periods = list(KyKeToan.objects.filter(nam=year).order_by('ky_so'))
        existing_count = KyKeToan.objects.filter(nam=year).count()
        current_period = KyKeToan.objects.filter(is_current=True).first()
    except (OperationalError, ProgrammingError):
        periods = []
        existing_count = 0
        current_period = None

    if not periods:
        periods = [SimpleNamespace(**row) for row in build_year_period_rows(year)]

    return render(request, 'so_cai/ky_ke_toan.html', {
        'page_title': 'Kỳ kế toán',
        'active_menu': 'ky_ke_toan',
        'year': year,
        'periods': periods,
        'existing_count': existing_count,
        'current_period': current_period,
    })


@login_required
def so_cai_view(request):
    today = date.today()
    from_date = _parse_date(request.GET.get('tu_ngay'), today.replace(day=1))
    to_date = _parse_date(request.GET.get('den_ngay'), today)
    account_code = (request.GET.get('tai_khoan') or '').strip()
    selected_account = TaiKhoanKeToan.objects.filter(ma_tk=account_code, trang_thai=True).first() if account_code else None

    report = {
        'account': None,
        'opening_balance': 0,
        'total_debit': 0,
        'total_credit': 0,
        'closing_balance': 0,
        'rows': [],
    }
    if account_code:
        report = get_general_ledger(
            account_code=account_code,
            from_date=from_date,
            to_date=to_date,
        )

    return render(request, 'so_cai/so_cai.html', {
        'page_title': 'So cai',
        'active_menu': 'so_cai',
        'from_date': from_date,
        'to_date': to_date,
        'account_code': account_code,
        'account_label': f'{selected_account.ma_tk} - {selected_account.ten_tk}' if selected_account else '',
        'report': report,
        'accounts': TaiKhoanKeToan.objects.filter(trang_thai=True).order_by('ma_tk'),
        'customers': KhachHang.objects.filter(trang_thai=True).order_by('ma_kh'),
        'suppliers': NhaCungCap.objects.filter(trang_thai=True).order_by('ma_ncc'),
    })


@login_required
def post_document_view(request):
    if request.method != 'POST':
        return redirect('so_cai')

    document_type = (request.POST.get('document_type') or '').strip()
    document_id = request.POST.get('document_id')

    if not str(document_id).isdigit():
        messages.error(request, 'ID chung tu khong hop le.')
        return redirect('so_cai')

    try:
        entry = post_to_ledger(document_type=document_type, document_id=int(document_id), user=request.user)
        messages.success(request, f'Da ghi so thanh cong: {entry.entry_number}')
    except LedgerPostingError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        messages.error(request, f'Khong the ghi so: {exc}')

    return redirect('so_cai')


@login_required
def post_to_ledger_api(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    document_type = (request.POST.get('document_type') or '').strip()
    document_id = request.POST.get('document_id')
    if not str(document_id).isdigit():
        return JsonResponse({'ok': False, 'message': 'document_id khong hop le'}, status=400)

    try:
        entry = post_to_ledger(document_type=document_type, document_id=int(document_id), user=request.user)
    except LedgerPostingError as exc:
        return JsonResponse({'ok': False, 'message': str(exc)}, status=400)

    return JsonResponse({'ok': True, 'entry_number': entry.entry_number, 'entry_id': entry.id})


@login_required
def general_ledger_api(request):
    account_code = (request.GET.get('account_code') or '').strip()
    if not account_code:
        return JsonResponse({'ok': False, 'message': 'Thieu account_code'}, status=400)

    today = date.today()
    from_date = _parse_date(request.GET.get('from_date'), today.replace(day=1))
    to_date = _parse_date(request.GET.get('to_date'), today)

    report = get_general_ledger(account_code, from_date, to_date)
    return JsonResponse({
        'ok': True,
        'account': report['account'].ma_tk if report['account'] else None,
        'opening_balance': float(report['opening_balance']),
        'total_debit': float(report['total_debit']),
        'total_credit': float(report['total_credit']),
        'closing_balance': float(report['closing_balance']),
        'rows': [
            {
                'posting_date': r['posting_date'].isoformat(),
                'document_date': r['document_date'].isoformat(),
                'entry_number': r['entry_number'],
                'document_type': r['document_type'],
                'document_number': r['document_number'],
                'description': r['description'],
                'debit': float(r['debit']),
                'credit': float(r['credit']),
                'running_balance': float(r['running_balance']),
            }
            for r in report['rows']
        ],
    })


@login_required
def trial_balance_api(request):
    today = date.today()
    from_date = _parse_date(request.GET.get('from_date'), today.replace(day=1))
    to_date = _parse_date(request.GET.get('to_date'), today)

    report = get_trial_balance(from_date, to_date)
    return JsonResponse({
        'ok': True,
        'from_date': from_date.isoformat(),
        'to_date': to_date.isoformat(),
        'total_period_debit': float(report['total_period_debit']),
        'total_period_credit': float(report['total_period_credit']),
        'rows': [
            {
                'account_code': r['account_code'],
                'account_name': r['account_name'],
                'opening_debit': float(r['opening_debit']),
                'opening_credit': float(r['opening_credit']),
                'period_debit': float(r['period_debit']),
                'period_credit': float(r['period_credit']),
                'opening_balance': float(r['opening_balance']),
                'closing_balance': float(r['closing_balance']),
            }
            for r in report['rows']
        ],
    })
