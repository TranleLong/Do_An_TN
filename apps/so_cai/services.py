from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Callable

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.ban_hang.models import HoaDonBan, PhieuThu, PhieuTraHang
from apps.danh_muc.models import TaiKhoanKeToan
from apps.kho.models import KiemKe, PhieuNhap, PhieuXuat, TonKho
from apps.so_cai.periods import ensure_accounting_period_open

from .models import JournalEntry, JournalEntryLine


@dataclass
class LedgerPayload:
    document_number: str
    document_date: date
    posting_date: date
    description: str
    customer_id: int | None
    supplier_id: int | None
    warehouse_id: int | None
    lines: list[dict]


class LedgerPostingError(ValueError):
    pass


def _as_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def _resolve_account(code: str, default_name: str = '') -> TaiKhoanKeToan:
    ma_tk = str(code or '').strip()
    if not ma_tk:
        raise LedgerPostingError('Thieu ma tai khoan but toan.')
    account, _ = TaiKhoanKeToan.objects.get_or_create(
        ma_tk=ma_tk,
        defaults={
            'ten_tk': default_name or f'Tai khoan {ma_tk}',
            'trang_thai': True,
        },
    )
    return account


def _next_entry_number() -> str:
    now = timezone.now()
    seed = now.strftime('%Y%m%d%H%M%S')
    prefix = f'GL-{seed}'
    last = JournalEntry.objects.filter(entry_number__startswith=prefix).count()
    return f'{prefix}-{last + 1:03d}'


def _validate_balanced(lines: list[dict]) -> None:
    tong_no = sum(_as_decimal(x.get('debit')) for x in lines)
    tong_co = sum(_as_decimal(x.get('credit')) for x in lines)
    if tong_no != tong_co:
        raise LedgerPostingError(f'Tong No ({tong_no}) khong bang Tong Co ({tong_co}).')
    if tong_no <= 0:
        raise LedgerPostingError('But toan khong co gia tri phat sinh.')


def _compact_lines(lines: list[dict]) -> list[dict]:
    grouped: dict[tuple, dict] = {}
    for item in lines:
        key = (
            str(item.get('account_code') or '').strip(),
            item.get('customer_id'),
            item.get('supplier_id'),
            item.get('warehouse_id'),
            str(item.get('note') or '').strip(),
        )
        if not key[0]:
            continue
        if key not in grouped:
            grouped[key] = {
                'account_code': key[0],
                'debit': Decimal('0'),
                'credit': Decimal('0'),
                'customer_id': key[1],
                'supplier_id': key[2],
                'warehouse_id': key[3],
                'note': key[4],
            }
        grouped[key]['debit'] += _as_decimal(item.get('debit'))
        grouped[key]['credit'] += _as_decimal(item.get('credit'))
    return [v for v in grouped.values() if v['debit'] > 0 or v['credit'] > 0]


def _invoice_payload(doc_id: int) -> LedgerPayload:
    hoa_don = HoaDonBan.objects.prefetch_related('chi_tiet').select_related('khach_hang').get(pk=doc_id)
    if str(hoa_don.trang_thai or '').strip() not in ('2', '3'):
        raise LedgerPostingError('Hoa don chua o trang thai da ghi so (2 - Chuyen so cai).')

    tong_truoc_thue = _as_decimal(hoa_don.tien_hang)
    tong_thue = _as_decimal(hoa_don.tong_tien_thue)
    tong_thanh_toan = _as_decimal(hoa_don.tong_cong)

    tk_no = str(hoa_don.tk_no or '131').strip()
    is_cash_invoice = tk_no in ('111', '112')
    lines: list[dict] = []

    if not is_cash_invoice:
        lines.append({
            'account_code': tk_no,
            'debit': tong_thanh_toan,
            'credit': Decimal('0'),
            'customer_id': hoa_don.khach_hang_id,
            'note': 'Ghi nhan cong no/thu tien hoa don',
            'warehouse_id': None,
        })

        doanh_thu_by_tk = defaultdict(Decimal)
        for ct in hoa_don.chi_tiet.all():
            tk_doanh_thu = str(ct.tk_doanh_thu or '511').strip() or '511'
            doanh_thu_by_tk[tk_doanh_thu] += _as_decimal(ct.tien_hang)

        for tk, amount in doanh_thu_by_tk.items():
            lines.append({
                'account_code': tk,
                'debit': Decimal('0'),
                'credit': amount,
                'customer_id': hoa_don.khach_hang_id,
                'note': 'Doanh thu ban hang',
                'warehouse_id': None,
            })

        if tong_thue > 0:
            lines.append({
                'account_code': '3331',
                'debit': Decimal('0'),
                'credit': tong_thue,
                'customer_id': hoa_don.khach_hang_id,
                'note': 'Thue GTGT dau ra',
                'warehouse_id': None,
            })

    # Gia von: No tk_gia_von / Co tk_kho (per line, default 632 / 156)

    for ct in hoa_don.chi_tiet.all():
        tk_gia_von = str(ct.tk_gia_von or '632').strip() or '632'
        tk_kho_co = str(getattr(ct, 'tk_kho', None) or '156').strip() or '156'
        ton = TonKho.objects.filter(hang_hoa_id=ct.hang_hoa_id, kho_id=ct.kho_id).first()
        gia_von_tb = _as_decimal(ton.gia_von_tb if ton else 0)
        gia_von_line = gia_von_tb * _as_decimal(ct.so_luong)
        if gia_von_line <= 0:
            continue
        lines.append({
            'account_code': tk_gia_von,
            'debit': gia_von_line,
            'credit': Decimal('0'),
            'customer_id': hoa_don.khach_hang_id,
            'note': 'Gia von hang ban',
            'warehouse_id': ct.kho_id,
        })
        lines.append({
            'account_code': tk_kho_co,
            'debit': Decimal('0'),
            'credit': gia_von_line,
            'customer_id': None,
            'note': 'Xuat kho gia von',
            'warehouse_id': ct.kho_id,
        })

    return LedgerPayload(
        document_number=hoa_don.so_hoa_don,
        document_date=hoa_don.ngay_lap,
        posting_date=hoa_don.ngay_hach_toan,
        description=hoa_don.dien_giai or f'Hoa don ban {hoa_don.so_hoa_don}',
        customer_id=hoa_don.khach_hang_id,
        supplier_id=None,
        warehouse_id=None,
        lines=_compact_lines(lines),
    )


def _receipt_payload(doc_id: int) -> LedgerPayload:
    phieu = PhieuThu.objects.select_related('khach_hang', 'hoa_don').get(pk=doc_id)
    if str(phieu.trang_thai or '').strip() not in ('2', '3'):
        raise LedgerPostingError('Phieu thu chua o trang thai da ghi so (2 - Chuyen so cai).')

    tk_no = '111' if getattr(phieu, 'hinh_thuc_thu', 'tien_mat') == 'tien_mat' else '112'
    so_tien = _as_decimal(phieu.tong_thu)

    lines = []

    hoa_don_lk = getattr(phieu, 'hoa_don', None)
    if hoa_don_lk and str(hoa_don_lk.tk_no or '').strip() in ('111', '112'):
        # Đây là hóa đơn thu tiền ngay, doanh thu & thuế chưa được ghi qua sổ cái lúc duyệt hóa đơn
        # Nên phiếu thu sẽ gánh việc ghi Nợ 111 / Có 511, 3331...
        doanh_thu_by_tk = defaultdict(Decimal)
        tong_thue = Decimal('0')
        for ct in hoa_don_lk.chi_tiet.all():
            tk_doanh_thu = str(ct.tk_doanh_thu or '511').strip() or '511'
            doanh_thu_by_tk[tk_doanh_thu] += _as_decimal(ct.tien_hang)
            tong_thue += _as_decimal(ct.tien_thue)
            
        lines.append({
            'account_code': tk_no,
            'debit': so_tien, 
            'credit': Decimal('0'),
            'customer_id': phieu.khach_hang_id,
            'note': 'Thu tien ban hang',
            'warehouse_id': None,
        })
        
        for tk, amount in doanh_thu_by_tk.items():
            lines.append({
                'account_code': tk,
                'debit': Decimal('0'),
                'credit': amount,
                'customer_id': phieu.khach_hang_id,
                'note': 'Doanh thu ban hang (tu hoa don)',
                'warehouse_id': None,
            })

        if tong_thue > 0:
            lines.append({
                'account_code': '3331',
                'debit': Decimal('0'),
                'credit': tong_thue,
                'customer_id': phieu.khach_hang_id,
                'note': 'Thue GTGT dau ra (tu hoa don)',
                'warehouse_id': None,
            })
    else:
        # Thu công nợ bình thường
        lines = _compact_lines([
            {
                'account_code': tk_no,
                'debit': so_tien,
                'credit': Decimal('0'),
                'customer_id': phieu.khach_hang_id,
                'note': 'Thu tien khach hang',
                'warehouse_id': None,
            },
            {
                'account_code': '131',
                'debit': Decimal('0'),
                'credit': so_tien,
                'customer_id': phieu.khach_hang_id,
                'note': 'Giam cong no khach hang',
                'warehouse_id': None,
            },
        ])


    return LedgerPayload(
        document_number=phieu.so_phieu,
        document_date=phieu.ngay_thu,
        posting_date=phieu.ngay_thu,
        description=phieu.ghi_chu or f'Phieu thu {phieu.so_phieu}',
        customer_id=phieu.khach_hang_id,
        supplier_id=None,
        warehouse_id=None,
        lines=lines,
    )


def _phieu_nhap_payload(doc_id: int) -> LedgerPayload:
    phieu = PhieuNhap.objects.prefetch_related('chi_tiet').select_related('nha_cung_cap', 'kho').get(pk=doc_id)
    if str(phieu.trang_thai or '').strip() not in ('2', '3'):
        raise LedgerPostingError('Phieu nhap chua o trang thai da ghi so (2 - So kho / 3 - So cai).')

    lines: list[dict] = []
    for ct in phieu.chi_tiet.all():
        so_tien = _as_decimal(ct.thanh_tien)
        tk_no = str(ct.tk_no or '156').strip() or '156'
        if ct.tk_co:
            tk_co = str(ct.tk_co).strip()
        elif phieu.loai_nhap == '1':
            tk_co = '331'
        else:
            tk_co = '111'

        lines.append({
            'account_code': tk_no,
            'debit': so_tien,
            'credit': Decimal('0'),
            'supplier_id': phieu.nha_cung_cap_id,
            'warehouse_id': phieu.kho_id,
            'note': 'Nhap kho',
        })
        lines.append({
            'account_code': tk_co,
            'debit': Decimal('0'),
            'credit': so_tien,
            'supplier_id': phieu.nha_cung_cap_id,
            'warehouse_id': phieu.kho_id,
            'note': 'Doi ung nhap kho',
        })

    return LedgerPayload(
        document_number=phieu.so_phieu,
        document_date=getattr(phieu, 'ngay_lap', None) or phieu.ngay_chung_tu,
        posting_date=getattr(phieu, 'ngay_hach_toan', None) or phieu.ngay_chung_tu,
        description=phieu.ghi_chu or f'Phieu nhap {phieu.so_phieu}',
        customer_id=None,
        supplier_id=phieu.nha_cung_cap_id,
        warehouse_id=phieu.kho_id,
        lines=_compact_lines(lines),
    )


def _phieu_xuat_payload(doc_id: int) -> LedgerPayload:
    phieu = PhieuXuat.objects.prefetch_related('chi_tiet').select_related('kho').get(pk=doc_id)
    if str(phieu.trang_thai or '').strip() not in ('2', '3'):
        raise LedgerPostingError('Phieu xuat chua o trang thai da ghi so (2 - So kho / 3 - So cai).')

    lines: list[dict] = []
    for ct in phieu.chi_tiet.all():
        gia_tri = _as_decimal(ct.tong_gia_von)
        if gia_tri <= 0:
            gia_tri = _as_decimal(ct.gia_von) * _as_decimal(ct.so_luong)

        tk_no = str(ct.tk_no or '632').strip() or '632'
        tk_co = str(ct.tk_co or '156').strip() or '156'

        lines.append({
            'account_code': tk_no,
            'debit': gia_tri,
            'credit': Decimal('0'),
            'warehouse_id': phieu.kho_id,
            'note': 'Gia von xuat kho',
        })
        lines.append({
            'account_code': tk_co,
            'debit': Decimal('0'),
            'credit': gia_tri,
            'warehouse_id': phieu.kho_id,
            'note': 'Xuat kho',
        })

    return LedgerPayload(
        document_number=phieu.so_phieu,
        document_date=getattr(phieu, 'ngay_lap', None) or phieu.ngay_chung_tu,
        posting_date=getattr(phieu, 'ngay_hach_toan', None) or phieu.ngay_chung_tu,
        description=phieu.ghi_chu or f'Phieu xuat {phieu.so_phieu}',
        customer_id=None,
        supplier_id=None,
        warehouse_id=phieu.kho_id,
        lines=_compact_lines(lines),
    )


def _kiem_ke_payload(doc_id: int) -> LedgerPayload:
    phieu = KiemKe.objects.prefetch_related('chi_tiet').select_related('kho').get(pk=doc_id)
    if str(phieu.trang_thai or '').strip() not in ('2', '3'):
        raise LedgerPostingError('Phieu dieu chinh kho chua o trang thai da ghi so (2 - Chờ điều chỉnh / 3 - Hoàn thành).')

    lines: list[dict] = []
    for ct in phieu.chi_tiet.all():
        chenh = int(ct.chenh_lech or 0)
        if chenh == 0:
            continue

        ton = TonKho.objects.filter(hang_hoa=ct.hang_hoa, kho=phieu.kho).first()
        gia_von = _as_decimal(ton.gia_von_tb if ton else 0)
        gia_tri = abs(chenh) * gia_von
        if gia_tri <= 0:
            continue

        if chenh > 0:
            # Tang ton: No 156 / Co 3381
            lines.append({
                'account_code': '156',
                'debit': gia_tri,
                'credit': Decimal('0'),
                'warehouse_id': phieu.kho_id,
                'note': 'Dieu chinh tang ton kho',
            })
            lines.append({
                'account_code': '3381',
                'debit': Decimal('0'),
                'credit': gia_tri,
                'warehouse_id': phieu.kho_id,
                'note': 'Doi ung dieu chinh tang ton',
            })
        else:
            # Giam ton: No 3381 / Co 156
            lines.append({
                'account_code': '3381',
                'debit': gia_tri,
                'credit': Decimal('0'),
                'warehouse_id': phieu.kho_id,
                'note': 'Dieu chinh giam ton kho',
            })
            lines.append({
                'account_code': '156',
                'debit': Decimal('0'),
                'credit': gia_tri,
                'warehouse_id': phieu.kho_id,
                'note': 'Doi ung dieu chinh giam ton',
            })

    return LedgerPayload(
        document_number=f'KK-{phieu.id}',
        document_date=phieu.ngay_kiem_ke,
        posting_date=phieu.ngay_kiem_ke,
        description=phieu.ghi_chu or f'Phieu dieu chinh kho {phieu.id}',
        customer_id=None,
        supplier_id=None,
        warehouse_id=phieu.kho_id,
        lines=_compact_lines(lines),
    )


def _return_payload(doc_id: int) -> LedgerPayload:
    phieu = PhieuTraHang.objects.prefetch_related('chi_tiet__hang_hoa').select_related('khach_hang').get(pk=doc_id)
    so_tien = _as_decimal(phieu.tong_tien_tra)
    if so_tien <= 0:
        raise LedgerPostingError('Phieu tra hang khong co gia tri but toan.')

    # Doanh thu giam (hoac 531)
    tk_no = (phieu.tk_no or '511').strip()
    tk_co = (phieu.tk_co or '131').strip()
    lines = [
        {
            'account_code': tk_no,
            'debit': so_tien,
            'credit': Decimal('0'),
            'customer_id': phieu.khach_hang_id,
            'note': 'Giam doanh thu hang ban bi tra lai',
        },
        {
            'account_code': tk_co,
            'debit': Decimal('0'),
            'credit': so_tien,
            'customer_id': phieu.khach_hang_id,
            'note': 'Doi ung giam doanh thu',
        },
    ]

    # Nhap lai gia von (156 / 632)
    tong_gia_von = Decimal('0')
    for ct in phieu.chi_tiet.all():
        gia_von_1 = ct.hang_hoa.get_gia_von() if hasattr(ct.hang_hoa, 'get_gia_von') else Decimal('0')
        tong_gia_von += Decimal(gia_von_1 or 0) * Decimal(ct.so_luong or 0)
    
    if tong_gia_von > 0:
        lines.append({
            'account_code': '156',
            'debit': tong_gia_von,
            'credit': Decimal('0'),
            'customer_id': None,
            'note': 'Nhap lai gia von hang tra lai',
        })
        lines.append({
            'account_code': '632',
            'debit': Decimal('0'),
            'credit': tong_gia_von,
            'customer_id': None,
            'note': 'Giam tru gia von hang ban',
        })

    lines = _compact_lines(lines)

    return LedgerPayload(
        document_number=phieu.so_phieu,
        document_date=phieu.ngay_tra,
        posting_date=phieu.ngay_tra,
        description=phieu.ly_do_tra or f'Hang ban bi tra lai {phieu.so_phieu}',
        customer_id=phieu.khach_hang_id,
        supplier_id=None,
        warehouse_id=None,
        lines=lines,
    )


PAYLOAD_BUILDERS: dict[str, Callable[[int], LedgerPayload]] = {
    'hoa_don_ban': _invoice_payload,
    'phieu_thu': _receipt_payload,
    'phieu_nhap': _phieu_nhap_payload,
    'phieu_xuat': _phieu_xuat_payload,
    'phieu_dieu_chinh_kho': _kiem_ke_payload,
    'hang_ban_tra_lai': _return_payload,
}


@transaction.atomic
def post_to_ledger(document_type: str, document_id: int, user=None) -> JournalEntry:
    if document_type not in PAYLOAD_BUILDERS:
        raise LedgerPostingError(f'Khong ho tro loai chung tu: {document_type}')

    existed = JournalEntry.objects.filter(
        document_type=document_type,
        document_id=document_id,
        status='posted',
    ).first()
    if existed:
        return existed

    payload = PAYLOAD_BUILDERS[document_type](document_id)
    payload.lines = _compact_lines(payload.lines)
    _validate_balanced(payload.lines)
    ensure_accounting_period_open(payload.posting_date, 'ghi sổ chứng từ')

    entry = JournalEntry.objects.create(
        entry_number=_next_entry_number(),
        document_type=document_type,
        document_id=document_id,
        document_number=payload.document_number,
        document_date=payload.document_date,
        posting_date=payload.posting_date,
        description=payload.description,
        customer_id=payload.customer_id,
        supplier_id=payload.supplier_id,
        warehouse_id=payload.warehouse_id,
        status='posted',
        posted_by=user if getattr(user, 'is_authenticated', False) else None,
    )

    for idx, line in enumerate(payload.lines, start=1):
        account = _resolve_account(str(line.get('account_code') or ''))
        JournalEntryLine.objects.create(
            journal_entry=entry,
            line_no=idx,
            account=account,
            debit_amount=_as_decimal(line.get('debit')),
            credit_amount=_as_decimal(line.get('credit')),
            customer_id=line.get('customer_id'),
            supplier_id=line.get('supplier_id'),
            warehouse_id=line.get('warehouse_id'),
            note=str(line.get('note') or ''),
        )

    if entry.total_debit != entry.total_credit:
        raise LedgerPostingError('Chung tu ghi so khong can doi No/Co sau khi luu.')

    return entry


@transaction.atomic
def reverse_entry(entry_id: int, user=None, reason: str = '') -> JournalEntry:
    original = JournalEntry.objects.select_for_update().get(pk=entry_id)
    if original.status != 'posted':
        raise LedgerPostingError('Chi duoc dao but toan da ghi so.')
    if original.reversed_entry_id:
        raise LedgerPostingError('Chung tu nay da duoc dao.')

    ensure_accounting_period_open(timezone.now().date(), 'đảo bút toán')

    reverse = JournalEntry.objects.create(
        entry_number=_next_entry_number(),
        document_type='dao_but_toan',
        document_id=original.id,
        document_number=f'DAO-{original.entry_number}',
        document_date=timezone.now().date(),
        posting_date=timezone.now().date(),
        description=reason or f'Dao but toan {original.entry_number}',
        customer=original.customer,
        supplier=original.supplier,
        warehouse=original.warehouse,
        status='posted',
        posted_by=user if getattr(user, 'is_authenticated', False) else None,
    )

    for idx, line in enumerate(original.lines.all(), start=1):
        JournalEntryLine.objects.create(
            journal_entry=reverse,
            line_no=idx,
            account=line.account,
            debit_amount=line.credit_amount,
            credit_amount=line.debit_amount,
            customer=line.customer,
            supplier=line.supplier,
            warehouse=line.warehouse,
            note=f'DAO: {line.note}',
        )

    original.status = 'reversed'
    original.reversed_entry = reverse
    original.save(update_fields=['status', 'reversed_entry', 'updated_at'])
    return reverse


def _normal_side(account_code: str) -> str:
    code = (account_code or '').strip()
    if not code:
        return 'D'
    return 'D' if code[:1] in {'1', '2', '6', '8'} else 'C'


def get_general_ledger(
    account_code: str,
    from_date: date,
    to_date: date,
    document_type: str | None = None,
    document_number: str | None = None,
    customer_id: int | None = None,
    supplier_id: int | None = None,
):
    account = TaiKhoanKeToan.objects.filter(ma_tk=account_code).first()
    if not account:
        return {
            'account': None,
            'opening_balance': Decimal('0'),
            'total_debit': Decimal('0'),
            'total_credit': Decimal('0'),
            'closing_balance': Decimal('0'),
            'rows': [],
        }

    base_qs = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
    ).select_related('journal_entry', 'customer', 'supplier', 'warehouse')

    if document_type:
        base_qs = base_qs.filter(journal_entry__document_type=document_type)
    if document_number:
        base_qs = base_qs.filter(journal_entry__document_number__icontains=document_number.strip())
    if customer_id:
        base_qs = base_qs.filter(customer_id=customer_id)
    if supplier_id:
        base_qs = base_qs.filter(supplier_id=supplier_id)

    opening_agg = base_qs.filter(journal_entry__posting_date__lt=from_date).aggregate(
        d=Sum('debit_amount'),
        c=Sum('credit_amount'),
    )
    opening_debit = _as_decimal(opening_agg['d'])
    opening_credit = _as_decimal(opening_agg['c'])

    normal = _normal_side(account.ma_tk)
    opening_balance = opening_debit - opening_credit if normal == 'D' else opening_credit - opening_debit

    period_qs = base_qs.filter(journal_entry__posting_date__range=[from_date, to_date]).order_by(
        'journal_entry__posting_date', 'journal_entry__entry_number', 'line_no', 'id'
    )

    running = opening_balance
    rows = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    for line in period_qs:
        d = _as_decimal(line.debit_amount)
        c = _as_decimal(line.credit_amount)
        total_debit += d
        total_credit += c
        running += (d - c) if normal == 'D' else (c - d)
        rows.append({
            'posting_date': line.journal_entry.posting_date,
            'document_date': line.journal_entry.document_date,
            'entry_number': line.journal_entry.entry_number,
            'document_type': line.journal_entry.document_type,
            'document_number': line.journal_entry.document_number,
            'description': line.journal_entry.description,
            'debit': d,
            'credit': c,
            'running_balance': running,
            'customer': line.customer.ten_kh if line.customer else '',
            'supplier': line.supplier.ten_ncc if line.supplier else '',
            'warehouse': line.warehouse.ten_kho if line.warehouse else '',
        })

    closing_balance = running

    return {
        'account': account,
        'opening_balance': opening_balance,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'closing_balance': closing_balance,
        'rows': rows,
    }


def get_trial_balance(from_date: date, to_date: date):
    lines = JournalEntryLine.objects.filter(
        journal_entry__status='posted',
        journal_entry__posting_date__lte=to_date,
    ).select_related('account', 'journal_entry')

    stats = defaultdict(lambda: {
        'account_code': '',
        'account_name': '',
        'opening_debit': Decimal('0'),
        'opening_credit': Decimal('0'),
        'period_debit': Decimal('0'),
        'period_credit': Decimal('0'),
    })

    for line in lines:
        code = line.account.ma_tk
        row = stats[code]
        row['account_code'] = code
        row['account_name'] = line.account.ten_tk
        posting_date = line.journal_entry.posting_date
        d = _as_decimal(line.debit_amount)
        c = _as_decimal(line.credit_amount)

        if posting_date < from_date:
            row['opening_debit'] += d
            row['opening_credit'] += c
        elif from_date <= posting_date <= to_date:
            row['period_debit'] += d
            row['period_credit'] += c

    result = []
    for code in sorted(stats.keys()):
        row = stats[code]
        normal = _normal_side(code)
        opening_balance = row['opening_debit'] - row['opening_credit'] if normal == 'D' else row['opening_credit'] - row['opening_debit']
        movement = row['period_debit'] - row['period_credit'] if normal == 'D' else row['period_credit'] - row['period_debit']
        closing_balance = opening_balance + movement

        result.append({
            **row,
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
        })

    total_period_debit = sum((r['period_debit'] for r in result), Decimal('0'))
    total_period_credit = sum((r['period_credit'] for r in result), Decimal('0'))

    return {
        'rows': result,
        'total_period_debit': total_period_debit,
        'total_period_credit': total_period_credit,
    }
