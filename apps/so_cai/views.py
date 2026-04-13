from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.danh_muc.models import KhachHang, NhaCungCap, TaiKhoanKeToan

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
def so_cai_view(request):
    today = date.today()
    from_date = _parse_date(request.GET.get('tu_ngay'), today.replace(day=1))
    to_date = _parse_date(request.GET.get('den_ngay'), today)
    account_code = (request.GET.get('tai_khoan') or '').strip()
    document_type = (request.GET.get('loai_ct') or '').strip()
    document_number = (request.GET.get('so_ct') or '').strip()
    customer_id = request.GET.get('khach_hang') or ''
    supplier_id = request.GET.get('nha_cung_cap') or ''

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
            document_type=document_type or None,
            document_number=document_number or None,
            customer_id=int(customer_id) if str(customer_id).isdigit() else None,
            supplier_id=int(supplier_id) if str(supplier_id).isdigit() else None,
        )

    return render(request, 'so_cai/so_cai.html', {
        'page_title': 'So cai',
        'active_menu': 'so_cai',
        'from_date': from_date,
        'to_date': to_date,
        'account_code': account_code,
        'document_type': document_type,
        'document_number': document_number,
        'customer_id': str(customer_id),
        'supplier_id': str(supplier_id),
        'report': report,
        'accounts': TaiKhoanKeToan.objects.filter(trang_thai=True).order_by('ma_tk'),
        'customers': KhachHang.objects.filter(trang_thai=True).order_by('ma_kh'),
        'suppliers': NhaCungCap.objects.filter(trang_thai=True).order_by('ma_ncc'),
        'doc_type_choices': [
            ('', 'Tat ca chung tu'),
            ('hoa_don_ban', 'Hoa don ban hang'),
            ('phieu_thu', 'Phieu thu'),
            ('phieu_nhap', 'Phieu nhap kho'),
            ('phieu_xuat', 'Phieu xuat kho'),
            ('phieu_dieu_chinh_kho', 'Phieu dieu chinh kho'),
            ('hang_ban_tra_lai', 'Hang ban bi tra lai'),
        ],
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
