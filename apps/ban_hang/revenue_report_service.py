from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import F, Q, Sum
from django.utils import timezone

from .models import DonBan_CT, HoaDonBan_CT, PhieuTraHang_CT

MONEY_ZERO = Decimal('0')


@dataclass(frozen=True)
class RevenueReportFilters:
    from_date: date
    to_date: date
    date_type: str = 'chung_tu'
    customer_id: int | None = None
    salesperson_code: str = ''
    product_id: int | None = None
    group_id: int | None = None
    warehouse_id: int | None = None

    @staticmethod
    def _parse_date(value: str | None, default: date) -> date:
        raw = (value or '').strip()
        if not raw:
            return default
        return date.fromisoformat(raw)

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        raw = (value or '').strip()
        if not raw:
            return None
        if not raw.isdigit():
            raise ValueError(f'Gia tri bo loc khong hop le: {raw}')
        return int(raw)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> 'RevenueReportFilters':
        today = timezone.localdate()
        start_default = today.replace(day=1)
        from_date = cls._parse_date(payload.get('from_date'), start_default)
        to_date = cls._parse_date(payload.get('to_date'), today)
        if from_date > to_date:
            raise ValueError('Tu ngay phai <= den ngay')

        date_type = (payload.get('date_type') or 'chung_tu').strip()
        if date_type not in ('chung_tu', 'hach_toan'):
            raise ValueError('date_type chi nhan chung_tu hoac hach_toan')

        salesperson_code = (payload.get('salesperson_code') or '').strip()
        return cls(
            from_date=from_date,
            to_date=to_date,
            date_type=date_type,
            customer_id=cls._parse_int(payload.get('customer_id')),
            salesperson_code=salesperson_code,
            product_id=cls._parse_int(payload.get('product_id')),
            group_id=cls._parse_int(payload.get('group_id')),
            warehouse_id=cls._parse_int(payload.get('warehouse_id')),
        )


class RevenueReportService:
    """Tinh bao cao doanh thu theo nghiep vu ERP.

    Rule chinh:
    - Doanh thu gop = tong tien hang + thue VAT (toan bo gia tri hoa don da ghi so).
    - Giam tru doanh thu = tien hang tra lai + thue VAT cua phieu tra.
    - Doanh thu thuan = Doanh thu gop - Giam tru.
    - Loi nhuan gop = Doanh thu thuan - Gia von hang ban.
    - Gia von uu tien gia_von luu tren DonBan_CT, neu khong co thi lay gia_von_tb tu TonKho.
    """

    POSTED_STATUS = '2'
    RETURN_COMPLETED_STATUS = '2'

    def __init__(self, filters: RevenueReportFilters) -> None:
        self.filters = filters
        self._unit_cost_map = self._build_unit_cost_map()
        self._product_cost_map = self._build_product_cost_map()

    @property
    def _invoice_date_field(self) -> str:
        if self.filters.date_type == 'hach_toan':
            return 'hoa_don__ngay_hach_toan'
        return 'hoa_don__ngay_lap'

    @property
    def _return_date_field(self) -> str:
        if self.filters.date_type == 'hach_toan':
            return 'phieu_tra__ngay_hach_toan'
        return 'phieu_tra__ngay_lap'

    def _build_unit_cost_map(self) -> dict[tuple[int, int], Decimal]:
        rows = (
            DonBan_CT.objects
            .values('don_ban_id', 'hang_hoa_id')
            .annotate(
                total_qty=Sum('so_luong'),
                total_cost=Sum(F('gia_von') * F('so_luong')),
            )
        )
        data: dict[tuple[int, int], Decimal] = {}
        for row in rows:
            qty = Decimal(row['total_qty'] or 0)
            if qty <= 0:
                continue
            total_cost = Decimal(row['total_cost'] or 0)
            data[(int(row['don_ban_id']), int(row['hang_hoa_id']))] = total_cost / qty
        return data

    def _build_product_cost_map(self) -> dict[int, Decimal]:
        from apps.kho.models import TonKho
        data: dict[int, Decimal] = {}
        for tk in TonKho.objects.values('hang_hoa_id', 'gia_von_tb'):
            hh_id = tk['hang_hoa_id']
            if hh_id not in data or tk['gia_von_tb']:
                data[int(hh_id)] = Decimal(tk['gia_von_tb'] or 0)
        return data

    def _get_unit_cost(self, don_ban_id: int | None, hang_hoa_id: int) -> Decimal:
        db_id = int(don_ban_id) if don_ban_id else 0
        hh_id = int(hang_hoa_id) if hang_hoa_id else 0
        cost = self._unit_cost_map.get((db_id, hh_id), MONEY_ZERO)
        if cost <= 0:
            cost = self._product_cost_map.get(hh_id, MONEY_ZERO)
        return cost

    def _invoice_detail_queryset(self):
        qs = (
            HoaDonBan_CT.objects
            .select_related(
                'hoa_don',
                'hoa_don__khach_hang',
                'hang_hoa',
                'hang_hoa__nhom_hang',
                'kho',
            )
            .filter(hoa_don__trang_thai=self.POSTED_STATUS)
            .filter(**{f'{self._invoice_date_field}__gte': self.filters.from_date})
            .filter(**{f'{self._invoice_date_field}__lte': self.filters.to_date})
        )

        if self.filters.customer_id:
            qs = qs.filter(hoa_don__khach_hang_id=self.filters.customer_id)
        if self.filters.salesperson_code:
            qs = qs.filter(hoa_don__ma_nv_ban_hang__iexact=self.filters.salesperson_code)
        if self.filters.product_id:
            qs = qs.filter(hang_hoa_id=self.filters.product_id)
        if self.filters.group_id:
            qs = qs.filter(hang_hoa__nhom_hang_id=self.filters.group_id)
        if self.filters.warehouse_id:
            qs = qs.filter(kho_id=self.filters.warehouse_id)
        return qs

    def _return_detail_queryset(self):
        qs = (
            PhieuTraHang_CT.objects
            .select_related(
                'phieu_tra',
                'phieu_tra__khach_hang',
                'phieu_tra__hoa_don_goc',
                'hoa_don_ct_goc',
                'hang_hoa',
                'hang_hoa__nhom_hang',
                'kho',
            )
            .filter(phieu_tra__trang_thai=self.RETURN_COMPLETED_STATUS)
            .filter(**{f'{self._return_date_field}__gte': self.filters.from_date})
            .filter(**{f'{self._return_date_field}__lte': self.filters.to_date})
        )

        if self.filters.customer_id:
            qs = qs.filter(phieu_tra__khach_hang_id=self.filters.customer_id)
        if self.filters.product_id:
            qs = qs.filter(hang_hoa_id=self.filters.product_id)
        if self.filters.group_id:
            qs = qs.filter(hang_hoa__nhom_hang_id=self.filters.group_id)
        if self.filters.warehouse_id:
            qs = qs.filter(kho_id=self.filters.warehouse_id)
        if self.filters.salesperson_code:
            qs = qs.filter(phieu_tra__hoa_don_goc__ma_nv_ban_hang__iexact=self.filters.salesperson_code)
        return qs

    @staticmethod
    def _safe_money(value: Decimal | None) -> Decimal:
        return Decimal(value or 0)

    def _empty_bucket(self) -> dict[str, Decimal]:
        return {
            'gross_revenue': MONEY_ZERO,   # tien_hang + tien_thue (toan bo HD)
            'revenue_deduction': MONEY_ZERO,  # tra lai + thue tra lai
            'net_revenue': MONEY_ZERO,
            'cogs': MONEY_ZERO,
            'gross_profit': MONEY_ZERO,
        }

    def get_revenue_summary(self, group_by: str = 'day') -> dict[str, Any]:
        if group_by not in ('day', 'month', 'year'):
            raise ValueError('group_by chi nhan day|month|year')

        invoice_lines = list(
            self._invoice_detail_queryset().values(
                self._invoice_date_field,
                'hoa_don__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',   # tien hang sau chiet khau, chua co thue
                'tien_thue',    # thue VAT
            )
        )
        return_lines = list(
            self._return_detail_queryset().values(
                self._return_date_field,
                'phieu_tra__hoa_don_goc__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',   # tien hang tra lai
                'hoa_don_ct_goc__thue_suat',    # % thue cua dong tra tu hoa don goc
                'don_gia',      # de tinh lai thue neu can
            )
        )

        period_map: dict[str, dict[str, Decimal]] = {}

        def period_key(dt: date) -> str:
            if group_by == 'year':
                return dt.strftime('%Y')
            if group_by == 'month':
                return dt.strftime('%Y-%m')
            return dt.strftime('%Y-%m-%d')

        for row in invoice_lines:
            dt = row[self._invoice_date_field]
            if not dt:
                continue
            key = period_key(dt)
            bucket = period_map.setdefault(key, self._empty_bucket())

            tien_hang = self._safe_money(row['thanh_tien'])
            tien_thue = self._safe_money(row['tien_thue'])
            # Doanh thu gop = tien hang + thue VAT
            bucket['gross_revenue'] += tien_hang + tien_thue

            unit_cost = self._get_unit_cost(row.get('hoa_don__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] += self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        for row in return_lines:
            dt = row[self._return_date_field]
            if not dt:
                continue
            key = period_key(dt)
            bucket = period_map.setdefault(key, self._empty_bucket())

            tien_hang_tra = self._safe_money(row['thanh_tien'])
            # Tinh thue cua phieu tra = tien_hang_tra * thue_suat%
            thue_suat = self._safe_money(row.get('hoa_don_ct_goc__thue_suat') or 0)
            tien_thue_tra = round(tien_hang_tra * thue_suat / Decimal('100'), 0)
            # Giam tru = tien hang tra + thue tra
            bucket['revenue_deduction'] += tien_hang_tra + tien_thue_tra

            unit_cost = self._get_unit_cost(row.get('phieu_tra__hoa_don_goc__don_ban_id'), row['hang_hoa_id'])
            # Tra hang giam gia von
            bucket['cogs'] -= self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        rows: list[dict[str, Any]] = []
        total_gross = MONEY_ZERO
        total_deduction = MONEY_ZERO
        total_cogs = MONEY_ZERO

        for key in sorted(period_map.keys()):
            item = period_map[key]
            net_revenue = item['gross_revenue'] - item['revenue_deduction']
            # Loi nhuan gop = Doanh thu thuan - Gia von
            gross_profit = net_revenue - item['cogs']
            rows.append({
                'period': key,
                'gross_revenue': item['gross_revenue'],
                'revenue_deduction': item['revenue_deduction'],
                'net_revenue': net_revenue,
                'cogs': item['cogs'],
                'gross_profit': gross_profit,
            })
            total_gross += item['gross_revenue']
            total_deduction += item['revenue_deduction']
            total_cogs += item['cogs']

        net_total = total_gross - total_deduction
        return {
            'group_by': group_by,
            'from_date': self.filters.from_date,
            'to_date': self.filters.to_date,
            'rows': rows,
            'totals': {
                'gross_revenue': total_gross,
                'revenue_deduction': total_deduction,
                'net_revenue': net_total,
                'cogs': total_cogs,
                'gross_profit': net_total - total_cogs,
            },
        }

    def get_revenue_by_customer(self) -> dict[str, Any]:
        invoice_lines = list(
            self._invoice_detail_queryset().values(
                'hoa_don__khach_hang_id',
                'hoa_don__khach_hang__ma_kh',
                'hoa_don__khach_hang__ten_kh',
                'hoa_don__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',
                'tien_thue',
            )
        )
        return_lines = list(
            self._return_detail_queryset().values(
                'phieu_tra__khach_hang_id',
                'phieu_tra__khach_hang__ma_kh',
                'phieu_tra__khach_hang__ten_kh',
                'phieu_tra__hoa_don_goc__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',
                'hoa_don_ct_goc__thue_suat',
            )
        )

        buckets: dict[str, dict[str, Any]] = {}

        def ensure_bucket(key: str, ma: str, ten: str) -> dict[str, Any]:
            if key not in buckets:
                buckets[key] = {
                    'customer_id': int(key) if key.isdigit() else None,
                    'customer_code': ma,
                    'customer_name': ten,
                    **self._empty_bucket(),
                }
            return buckets[key]

        for row in invoice_lines:
            key = str(row['hoa_don__khach_hang_id'] or '0')
            bucket = ensure_bucket(key, row['hoa_don__khach_hang__ma_kh'] or '', row['hoa_don__khach_hang__ten_kh'] or 'Khach le')
            tien_hang = self._safe_money(row['thanh_tien'])
            tien_thue = self._safe_money(row['tien_thue'])
            bucket['gross_revenue'] += tien_hang + tien_thue
            
            unit_cost = self._get_unit_cost(row.get('hoa_don__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] += self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        for row in return_lines:
            key = str(row['phieu_tra__khach_hang_id'] or '0')
            bucket = ensure_bucket(key, row['phieu_tra__khach_hang__ma_kh'] or '', row['phieu_tra__khach_hang__ten_kh'] or 'Khach le')
            tien_hang_tra = self._safe_money(row['thanh_tien'])
            thue_suat = self._safe_money(row.get('hoa_don_ct_goc__thue_suat') or 0)
            tien_thue_tra = round(tien_hang_tra * thue_suat / Decimal('100'), 0)
            bucket['revenue_deduction'] += tien_hang_tra + tien_thue_tra
            
            unit_cost = self._get_unit_cost(row.get('phieu_tra__hoa_don_goc__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] -= self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        rows: list[dict[str, Any]] = []
        for key in sorted(buckets.keys(), key=lambda k: buckets[k]['gross_revenue'], reverse=True):
            item = buckets[key]
            item['net_revenue'] = item['gross_revenue'] - item['revenue_deduction']
            item['gross_profit'] = item['net_revenue'] - item['cogs']
            rows.append(item)

        return {
            'from_date': self.filters.from_date,
            'to_date': self.filters.to_date,
            'rows': rows,
        }

    def get_revenue_by_product(self) -> dict[str, Any]:
        invoice_lines = list(
            self._invoice_detail_queryset().values(
                'hang_hoa_id',
                'hang_hoa__ma_hang',
                'hang_hoa__ten_hang',
                'hang_hoa__nhom_hang__ten_nhom',
                'hoa_don__don_ban_id',
                'so_luong',
                'thanh_tien',
                'tien_thue',
            )
        )
        return_lines = list(
            self._return_detail_queryset().values(
                'hang_hoa_id',
                'hang_hoa__ma_hang',
                'hang_hoa__ten_hang',
                'hang_hoa__nhom_hang__ten_nhom',
                'phieu_tra__hoa_don_goc__don_ban_id',
                'so_luong',
                'thanh_tien',
                'hoa_don_ct_goc__thue_suat',
            )
        )

        buckets: dict[int, dict[str, Any]] = {}

        def ensure_bucket(row: dict[str, Any]) -> dict[str, Any]:
            product_id = int(row['hang_hoa_id'])
            if product_id not in buckets:
                buckets[product_id] = {
                    'product_id': product_id,
                    'product_code': row['hang_hoa__ma_hang'] or '',
                    'product_name': row['hang_hoa__ten_hang'] or '',
                    'group_name': row['hang_hoa__nhom_hang__ten_nhom'] or '',
                    'sold_qty': Decimal('0'),
                    'returned_qty': Decimal('0'),
                    **self._empty_bucket(),
                }
            return buckets[product_id]

        for row in invoice_lines:
            bucket = ensure_bucket(row)
            qty = Decimal(row['so_luong'] or 0)
            bucket['sold_qty'] += qty
            tien_hang = self._safe_money(row['thanh_tien'])
            tien_thue = self._safe_money(row['tien_thue'])
            bucket['gross_revenue'] += tien_hang + tien_thue
            
            unit_cost = self._get_unit_cost(row.get('hoa_don__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] += self._safe_money(qty * unit_cost)

        for row in return_lines:
            bucket = ensure_bucket(row)
            qty = Decimal(row['so_luong'] or 0)
            bucket['returned_qty'] += qty
            tien_hang_tra = self._safe_money(row['thanh_tien'])
            thue_suat = self._safe_money(row.get('hoa_don_ct_goc__thue_suat') or 0)
            tien_thue_tra = round(tien_hang_tra * thue_suat / Decimal('100'), 0)
            bucket['revenue_deduction'] += tien_hang_tra + tien_thue_tra
            
            unit_cost = self._get_unit_cost(row.get('phieu_tra__hoa_don_goc__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] -= self._safe_money(qty * unit_cost)

        rows: list[dict[str, Any]] = []
        for product_id in sorted(buckets.keys(), key=lambda pid: buckets[pid]['net_revenue'], reverse=True):
            item = buckets[product_id]
            item['net_revenue'] = item['gross_revenue'] - item['revenue_deduction']
            item['gross_profit'] = item['net_revenue'] - item['cogs']
            rows.append(item)

        return {
            'from_date': self.filters.from_date,
            'to_date': self.filters.to_date,
            'rows': rows,
        }

    def get_revenue_by_salesperson(self) -> dict[str, Any]:
        invoice_lines = list(
            self._invoice_detail_queryset().values(
                'hoa_don__ma_nv_ban_hang',
                'hoa_don__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',
                'tien_thue',
            )
        )
        return_lines = list(
            self._return_detail_queryset().values(
                'phieu_tra__hoa_don_goc__ma_nv_ban_hang',
                'phieu_tra__hoa_don_goc__don_ban_id',
                'hang_hoa_id',
                'so_luong',
                'thanh_tien',
                'hoa_don_ct_goc__thue_suat',
            )
        )

        buckets: dict[str, dict[str, Any]] = {}

        def ensure_bucket(code: str) -> dict[str, Any]:
            key = (code or '').strip() or 'UNKNOWN'
            if key not in buckets:
                buckets[key] = {
                    'salesperson_code': key,
                    **self._empty_bucket(),
                }
            return buckets[key]

        for row in invoice_lines:
            bucket = ensure_bucket(row['hoa_don__ma_nv_ban_hang'] or '')
            tien_hang = self._safe_money(row['thanh_tien'])
            tien_thue = self._safe_money(row['tien_thue'])
            bucket['gross_revenue'] += tien_hang + tien_thue
            
            unit_cost = self._get_unit_cost(row.get('hoa_don__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] += self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        for row in return_lines:
            bucket = ensure_bucket(row['phieu_tra__hoa_don_goc__ma_nv_ban_hang'] or '')
            tien_hang_tra = self._safe_money(row['thanh_tien'])
            thue_suat = self._safe_money(row.get('hoa_don_ct_goc__thue_suat') or 0)
            tien_thue_tra = round(tien_hang_tra * thue_suat / Decimal('100'), 0)
            bucket['revenue_deduction'] += tien_hang_tra + tien_thue_tra
            
            unit_cost = self._get_unit_cost(row.get('phieu_tra__hoa_don_goc__don_ban_id'), row['hang_hoa_id'])
            bucket['cogs'] -= self._safe_money(Decimal(row['so_luong'] or 0) * unit_cost)

        rows: list[dict[str, Any]] = []
        for key in sorted(buckets.keys(), key=lambda k: buckets[k]['gross_revenue'], reverse=True):
            item = buckets[key]
            item['net_revenue'] = item['gross_revenue'] - item['revenue_deduction']
            item['gross_profit'] = item['net_revenue'] - item['cogs']
            rows.append(item)

        return {
            'from_date': self.filters.from_date,
            'to_date': self.filters.to_date,
            'rows': rows,
        }
