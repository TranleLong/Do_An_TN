from decimal import Decimal

from apps.kho.models import PhieuNhap

mapping = {
    'PNSEED001': Decimal('82000'),
    'PNSEED002': Decimal('84000'),
    'PNSEED003': Decimal('86000'),
}

updated = 0
for so_phieu, don_gia in mapping.items():
    phieu = PhieuNhap.objects.filter(so_phieu=so_phieu).first()
    if not phieu:
        continue
    for ct in phieu.chi_tiet.all():
        ct.don_gia = don_gia
        ct.save(update_fields=['don_gia'])
    phieu.tinh_tong()
    updated += 1

print(f'updated={updated}')
