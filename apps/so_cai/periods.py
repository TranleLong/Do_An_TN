from __future__ import annotations

from datetime import date, timedelta
from functools import wraps

from django.apps import apps
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver
from django.shortcuts import redirect


class AccountingPeriodError(ValidationError):
    pass


def _period_model():
    return apps.get_model('so_cai', 'KyKeToan')


def get_current_accounting_period():
    period_model = _period_model()
    try:
        return period_model.objects.filter(is_current=True).order_by('-nam', '-ky_so').first()
    except (OperationalError, ProgrammingError):
        return None


def get_accounting_period(target_date: date):
    if not target_date:
        return None
    if isinstance(target_date, str):
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return None
    period_model = _period_model()
    try:
        return period_model.objects.filter(tu_ngay__lte=target_date, den_ngay__gte=target_date).first()
    except (OperationalError, ProgrammingError):
        return None


def _coerce_dates(target_dates):
    for target_date in target_dates:
        if target_date:
            if isinstance(target_date, str):
                try:
                    target_date = date.fromisoformat(target_date)
                except ValueError:
                    continue
            yield target_date


def _format_period_name(period):
    if not period:
        return ''
    return f'{period.ky_so:02d}/{period.nam}'


def _build_period_error_message(*, current_period=None, first_invalid=None, missing_period_date=None):
    if missing_period_date:
        return (
            f'Chưa tạo kỳ kế toán cho ngày {missing_period_date:%d/%m/%Y}. '
            'Vui lòng chuyển sang đúng kỳ trước khi thao tác.'
        )

    period_name = _format_period_name(current_period)
    period_text = f' {period_name}' if period_name else ''

    if first_invalid:
        return (
            f'Chứng từ có ngày {first_invalid:%d/%m/%Y} đang ngoài kỳ kế toán{period_text}. '
            'Vui lòng chuyển sang đúng kỳ trước khi thao tác.'
        )

    return f'Chứng từ đang ngoài kỳ kế toán{period_text}. Vui lòng chuyển sang đúng kỳ trước khi thao tác.'


def ensure_accounting_period_open_for_dates(target_dates, document_label: str = 'chứng từ'):
    dates = list(_coerce_dates(target_dates))
    current_period = get_current_accounting_period()
    if current_period:
        if current_period.trang_thai == 'locked':
            raise AccountingPeriodError(_build_period_error_message(current_period=current_period))
        invalid_dates = [target_date for target_date in dates if not (current_period.tu_ngay <= target_date <= current_period.den_ngay)]
        if invalid_dates:
            first_invalid = invalid_dates[0]
            raise AccountingPeriodError(
                _build_period_error_message(current_period=current_period, first_invalid=first_invalid)
            )
        return current_period

    if not dates:
        return None

    periods = [get_accounting_period(target_date) for target_date in dates]
    if any(period is None for period in periods):
        return None
    if not all(periods):
        first_date = dates[0]
        raise AccountingPeriodError(_build_period_error_message(missing_period_date=first_date))

    opened_period = periods[0]
    if any(period.trang_thai == 'locked' for period in periods):
        raise AccountingPeriodError(_build_period_error_message(current_period=opened_period))
    return opened_period


def ensure_accounting_period_open(target_date: date, document_label: str = 'chứng từ'):
    return ensure_accounting_period_open_for_dates([target_date], document_label)


def guard_accounting_period_error(fallback_url_name: str | None = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except AccountingPeriodError as exc:
                messages.add_message(request, messages.ERROR, str(exc), extra_tags='period-lock')
                target = request.META.get('HTTP_REFERER') or ''
                if target:
                    return redirect(target)
                if fallback_url_name:
                    return redirect(fallback_url_name)
                return redirect('/')

        return wrapped

    return decorator


def build_year_period_rows(year: int):
    def end_of_month(first_day: date):
        next_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
        return next_month - timedelta(days=1)

    rows = []
    for month in range(1, 13):
        start_day = date(year, month, 1)
        rows.append({
            'nam': year,
            'ky_so': month,
            'ten_ky': f'Kỳ {month:02d}/{year}',
            'tu_ngay': start_day,
            'den_ngay': end_of_month(start_day),
            'trang_thai': 'open',
        })
    return rows


class AccountingPeriodLockMixin(models.Model):
    accounting_period_date_field: str = ''
    accounting_period_label: str = 'chứng từ'

    class Meta:
        abstract = True

    def _accounting_period_date(self):
        field_name = getattr(self, 'accounting_period_date_field', '')
        if not field_name:
            return None
        return getattr(self, field_name, None)

    def _ensure_accounting_period_open(self):
        period_date = self._accounting_period_date()
        if period_date:
            ensure_accounting_period_open(period_date, self.accounting_period_label)

    def save(self, *args, **kwargs):
        self._ensure_accounting_period_open()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._ensure_accounting_period_open()
        return super().delete(*args, **kwargs)


@receiver(pre_delete)
def block_bulk_delete_in_locked_period(sender, instance, using, **kwargs):
    if not isinstance(instance, AccountingPeriodLockMixin):
        return
    period_date = instance._accounting_period_date()
    if period_date:
        ensure_accounting_period_open(period_date, instance.accounting_period_label)
