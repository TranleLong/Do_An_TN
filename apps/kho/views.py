"""Views cho app Kho: PhieuXuat, TonKho, KiemKe, SoDo, TinhGia, DoiChieu"""
import re
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from openpyxl import Workbook

from apps.danh_muc.models import (HangHoa, KhachHang, Kho, NhaCungCap,
                                  TaiKhoanKeToan, ViTriKho)

from .models import (KiemKe, KiemKe_CT, MucTonKho, PhieuNhap, PhieuNhap_CT,
                     PhieuXuat, PhieuXuat_CT, TonKho, TonKhoViTri)

SLOT_TAG_REGEX = re.compile(r"\[SLOT=(?P<size>[1-5])\]")
SUC_CHUA_O_MAC_DINH = 50


def _can_access_inventory(user):
    return user.is_superuser or user.is_staff or user.has_perm('kho.view_tonkho')


def _recalculate_weighted_average(kho_id=None, hang_hoa_id=None):
    nhap_ct_qs = PhieuNhap_CT.objects.select_related('phieu_nhap').filter(
        phieu_nhap__trang_thai__in=('2', '3')
    )
    xuat_ct_qs = PhieuXuat_CT.objects.select_related('phieu_xuat').filter(
        phieu_xuat__trang_thai__in=('2', '3')
    )

    if kho_id:
        nhap_ct_qs = nhap_ct_qs.filter(phieu_nhap__kho_id=kho_id)
        xuat_ct_qs = xuat_ct_qs.filter(phieu_xuat__kho_id=kho_id)
    if hang_hoa_id:
        nhap_ct_qs = nhap_ct_qs.filter(hang_hoa_id=hang_hoa_id)
        xuat_ct_qs = xuat_ct_qs.filter(hang_hoa_id=hang_hoa_id)

    movements = []
    for ct in nhap_ct_qs.order_by('phieu_nhap__ngay_chung_tu', 'phieu_nhap_id', 'id'):
        movements.append({
            'type': 'N',
            'kho_id': ct.phieu_nhap.kho_id,
            'hang_hoa_id': ct.hang_hoa_id,
            'date': ct.phieu_nhap.ngay_chung_tu,
            'qty': int(ct.so_luong_nhan or 0),
            'unit_price': Decimal(ct.don_gia or 0),
            'obj': ct,
        })

    for ct in xuat_ct_qs.order_by('phieu_xuat__ngay_chung_tu', 'phieu_xuat_id', 'id'):
        movements.append({
            'type': 'X',
            'kho_id': ct.phieu_xuat.kho_id,
            'hang_hoa_id': ct.hang_hoa_id,
            'date': ct.phieu_xuat.ngay_chung_tu,
            'qty': int(ct.so_luong or 0),
            'unit_price': Decimal(0),
            'obj': ct,
        })

    movements.sort(key=lambda m: (m['date'], 0 if m['type'] == 'N' else 1, m['obj'].id))

    state = {}
    touched_keys = set()
    errors = []

    for mv in movements:
        key = (mv['kho_id'], mv['hang_hoa_id'])
        touched_keys.add(key)
        if key not in state:
            state[key] = {'qty': Decimal(0), 'value': Decimal(0)}
        st = state[key]

        if mv['qty'] <= 0:
            continue

        if mv['type'] == 'N':
            st['qty'] += Decimal(mv['qty'])
            st['value'] += Decimal(mv['qty']) * mv['unit_price']
            continue

        if st['qty'] <= 0 or st['qty'] < Decimal(mv['qty']):
            errors.append({
                'kho_id': mv['kho_id'],
                'hang_hoa_id': mv['hang_hoa_id'],
                'so_luong_xuat': mv['qty'],
                'so_luong_hien_co': int(st['qty']),
            })
            continue

        avg = (st['value'] / st['qty']) if st['qty'] > 0 else Decimal(0)
        mv['obj'].gia_von = round(avg, 0)
        mv['obj'].tong_gia_von = round(avg * Decimal(mv['qty']), 0)
        mv['obj'].save(update_fields=['gia_von', 'tong_gia_von'])

        st['qty'] -= Decimal(mv['qty'])
        st['value'] -= avg * Decimal(mv['qty'])

    if errors:
        return False, errors, 0

    updated = 0
    for kho_key, hang_key in touched_keys:
        st = state.get((kho_key, hang_key), {'qty': Decimal(0), 'value': Decimal(0)})
        qty = int(st['qty'])
        if qty > 0:
            avg = round(st['value'] / Decimal(qty), 0)
        else:
            avg = Decimal(0)

        ton_obj, _ = TonKho.objects.get_or_create(
            kho_id=kho_key,
            hang_hoa_id=hang_key,
            defaults={'so_luong': 0, 'so_luong_loi': 0, 'gia_von_tb': 0},
        )
        ton_obj.so_luong = qty
        ton_obj.gia_von_tb = avg
        ton_obj.save(update_fields=['so_luong', 'gia_von_tb', 'ngay_cap_nhat'])
        updated += 1

    for phieu in PhieuXuat.objects.filter(trang_thai__in=('2', '3')):
        if kho_id and phieu.kho_id != int(kho_id):
            continue
        tong = phieu.chi_tiet.aggregate(t=Sum('tong_gia_von'))['t'] or 0
        phieu.tong_gia_von = tong
        phieu.save(update_fields=['tong_gia_von'])

    return True, [], updated


def _extract_so_don_from_ghi_chu(ghi_chu):
    text = (ghi_chu or '').strip()
    if not text:
        return None
    m = re.search(r'xuất từ đơn\s+(.+?)(?:\s+-|$)', text, flags=re.IGNORECASE)
    if not m:
        return None
    return (m.group(1) or '').strip() or None


def _phieu_xuat_has_related_documents(phieu):
    if phieu.loai_xuat != 'ban_hang':
        return False

    from apps.ban_hang.models import DonBan

    so_don = _extract_so_don_from_ghi_chu(phieu.ghi_chu)
    if so_don:
        return DonBan.objects.filter(so_don=so_don, trang_thai__in=('2', '3')).exists()
    return False


def _rollback_phieu_nhap_inventory(phieu):
    if phieu.trang_thai not in ('2', '3'):
        return True, ''

    for ct in phieu.chi_tiet.select_related('hang_hoa'):
        ton = TonKho.objects.select_for_update().filter(hang_hoa=ct.hang_hoa, kho=phieu.kho).first()
        sl_hien_tai = int(ton.so_luong or 0) if ton else 0
        sl_can_hoan = int(ct.so_luong_nhan or 0)
        if sl_can_hoan > sl_hien_tai:
            return False, (
                f'Không thể sửa/xóa phiếu {phieu.so_phieu}: hàng {ct.hang_hoa.ma_hang} đã phát sinh chứng từ liên quan.'
            )

    for ct in phieu.chi_tiet.select_related('hang_hoa'):
        ton = TonKho.objects.select_for_update().filter(hang_hoa=ct.hang_hoa, kho=phieu.kho).first()
        if not ton:
            continue
        ton.so_luong = int(ton.so_luong or 0) - int(ct.so_luong_nhan or 0)
        if ton.so_luong < 0:
            ton.so_luong = 0
        ton.save(update_fields=['so_luong', 'ngay_cap_nhat'])

        con_lai_can_tru = int(ct.so_luong_nhan or 0)
        vt_rows = list(
            TonKhoViTri.objects.select_for_update().filter(hang_hoa=ct.hang_hoa, kho=phieu.kho, so_luong__gt=0)
            .order_by('-so_luong', 'id')
        )
        for vt in vt_rows:
            if con_lai_can_tru <= 0:
                break
            tru = min(int(vt.so_luong or 0), con_lai_can_tru)
            vt.so_luong = int(vt.so_luong or 0) - tru
            vt.save(update_fields=['so_luong', 'ngay_cap_nhat'])
            con_lai_can_tru -= tru

    phieu.trang_thai = '1'
    phieu.save(update_fields=['trang_thai'])
    return True, ''


def _rollback_phieu_xuat_inventory(phieu):
    if phieu.trang_thai not in ('2', '3'):
        return True, ''

    for ct in phieu.chi_tiet.select_related('hang_hoa'):
        ton, _ = TonKho.objects.select_for_update().get_or_create(
            hang_hoa=ct.hang_hoa,
            kho=phieu.kho,
            defaults={'so_luong': 0, 'gia_von_tb': ct.gia_von or 0},
        )
        ton.so_luong = int(ton.so_luong or 0) + int(ct.so_luong or 0)
        ton.save(update_fields=['so_luong', 'ngay_cap_nhat'])

    phieu.trang_thai = '1'
    phieu.save(update_fields=['trang_thai'])
    return True, ''


def _xac_nhan_phieu_xuat(phieu):
    if phieu.trang_thai != '1':
        return False, 'Chỉ phiếu nháp (bước 1) mới được xác nhận ghi Sổ kho'

    tong_gv = 0
    for ct in phieu.chi_tiet.select_related('hang_hoa'):
        ton = TonKho.objects.select_for_update().filter(hang_hoa=ct.hang_hoa, kho=phieu.kho).first()
        if not ton or ton.so_luong < ct.so_luong:
            return False, f'Không đủ tồn kho để xuất: {ct.hang_hoa.ten_hang}'

        ct.gia_von = ton.gia_von_tb
        ct.tong_gia_von = ton.gia_von_tb * ct.so_luong
        ct.save(update_fields=['gia_von', 'tong_gia_von'])

        ton.so_luong -= ct.so_luong
        ton.save(update_fields=['so_luong', 'ngay_cap_nhat'])
        tong_gv += ct.tong_gia_von

    phieu.tong_gia_von = tong_gv
    phieu.trang_thai = '2'
    phieu.save(update_fields=['tong_gia_von', 'trang_thai'])
    return True, ''


def _gen_so_phieu(prefix):
    now = timezone.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"


def _hang_slot_size(hang_hoa):
    m = SLOT_TAG_REGEX.search((hang_hoa.ghi_chu or '').upper())
    if not m:
        return 1
    return int(m.group('size'))


def _normalize_loai_nhap(value):
    mapping = {
        '1': '1',
        '2': '2',
        '3': '3',
        'mua_ncc': '1',
        'tra_hang_kh': '2',
        'dieu_chinh': '3',
    }
    return mapping.get(str(value or '').strip(), '1')


def _de_xuat_vi_tri_nhap(kho_id, hang_hoa, so_luong_nhap):
    rows = ViTriKho.objects.filter(kho_id=kho_id, trang_thai='hoat_dong').order_by('ma_vi_tri')
    if hang_hoa.loai_o_phu_hop:
        rows = rows.filter(loai_o=hang_hoa.loai_o_phu_hop)
    rows = list(rows)

    if not rows:
        return {
            'so_o_can': 0,
            'suc_chua_moi_o': SUC_CHUA_O_MAC_DINH,
            'de_xuat': [],
            'khong_hop_le': ['Không tìm thấy ô phù hợp theo loại ô'],
        }

    muc_chiem_cho = max(1, int(getattr(hang_hoa, 'muc_chiem_cho', 1) or 1))
    tong_dung_luong_can = int(so_luong_nhap) * muc_chiem_cho
    suggestions = []
    invalid_reasons = []

    for vi_tri in rows:
        ton_rows = list(TonKhoViTri.objects.filter(vi_tri=vi_tri).select_related('hang_hoa'))
        dung_luong_da_dung = sum(int(r.so_luong or 0) * max(1, int(getattr(r.hang_hoa, 'muc_chiem_cho', 1) or 1)) for r in ton_rows)
        suc_chua_toi_da = int(vi_tri.suc_chua_toi_da or SUC_CHUA_O_MAC_DINH)
        dung_luong_con_lai = max(0, suc_chua_toi_da - dung_luong_da_dung)
        so_luong_toi_da_co_the_nhap = dung_luong_con_lai // muc_chiem_cho
        if so_luong_toi_da_co_the_nhap <= 0:
            continue

        so_luong_cung_ma = sum(int(r.so_luong or 0) for r in ton_rows if r.hang_hoa_id == hang_hoa.id)
        uu_tien = 1 if so_luong_cung_ma > 0 else 0
        suggestions.append({
            'ma_vi_tri': vi_tri.ma_vi_tri,
            'vi_tri_id': vi_tri.id,
            'dung_luong_con_lai': dung_luong_con_lai,
            'so_luong_toi_da_co_the_nhap': int(so_luong_toi_da_co_the_nhap),
            'uu_tien': uu_tien,
        })

    suggestions.sort(key=lambda x: (-x['uu_tien'], -x['so_luong_toi_da_co_the_nhap'], x['ma_vi_tri']))

    con_lai = int(so_luong_nhap)
    de_xuat = []
    for row in suggestions:
        if con_lai <= 0:
            break
        phan_bo = min(con_lai, row['so_luong_toi_da_co_the_nhap'])
        if phan_bo <= 0:
            continue
        de_xuat.append({
            'ma_vi_tri': row['ma_vi_tri'],
            'vi_tri_id': row['vi_tri_id'],
            'de_xuat_so_luong': phan_bo,
            'dung_luong_con_lai': row['dung_luong_con_lai'],
        })
        con_lai -= phan_bo

    so_o_can = (tong_dung_luong_can + SUC_CHUA_O_MAC_DINH - 1) // SUC_CHUA_O_MAC_DINH
    return {
        'so_o_can': so_o_can,
        'suc_chua_moi_o': SUC_CHUA_O_MAC_DINH,
        'muc_chiem_cho': muc_chiem_cho,
        'tong_dung_luong_can': tong_dung_luong_can,
        'de_xuat': de_xuat,
        'con_lai_chua_phan_bo': con_lai,
        'khong_hop_le': invalid_reasons[:5],
    }


def _ghi_nhan_phan_bo_vi_tri(phieu_nhap):
    so_dong = 0
    for ct in phieu_nhap.chi_tiet.select_related('hang_hoa'):
        so_luong = int(ct.so_luong_nhan or 0)
        if so_luong <= 0:
            continue

        ket_qua = _de_xuat_vi_tri_nhap(phieu_nhap.kho_id, ct.hang_hoa, so_luong)
        for de_xuat in ket_qua['de_xuat']:
            vi_tri = ViTriKho.objects.filter(kho_id=phieu_nhap.kho_id, ma_vi_tri=de_xuat['ma_vi_tri']).first()
            if not vi_tri:
                continue
            obj, _ = TonKhoViTri.objects.get_or_create(
                hang_hoa=ct.hang_hoa,
                kho_id=phieu_nhap.kho_id,
                vi_tri=vi_tri,
                defaults={'so_luong': 0},
            )
            obj.so_luong += int(de_xuat['de_xuat_so_luong'])
            obj.save(update_fields=['so_luong', 'ngay_cap_nhat'])
            so_dong += 1
    return so_dong


@login_required
def goi_y_vi_tri_nhap(request):
    kho_id = request.GET.get('kho_id')
    hang_id = request.GET.get('hang_id')
    so_luong = request.GET.get('so_luong')

    try:
        so_luong = int(so_luong or 0)
    except (TypeError, ValueError):
        so_luong = 0

    if not kho_id or not hang_id or so_luong <= 0:
        return JsonResponse({'error': 'Thiếu dữ liệu đầu vào hợp lệ'}, status=400)

    hang_hoa = get_object_or_404(HangHoa, pk=hang_id)
    ket_qua = _de_xuat_vi_tri_nhap(kho_id, hang_hoa, so_luong)
    return JsonResponse({
        'ma_hang': hang_hoa.ma_hang,
        'ten_hang': hang_hoa.ten_hang,
        'so_luong_nhap': so_luong,
        **ket_qua,
    })


@login_required
def chi_tiet_vi_tri(request, pk):
    vi_tri = get_object_or_404(ViTriKho.objects.select_related('kho'), pk=pk)
    ton_rows = list(TonKhoViTri.objects.filter(vi_tri=vi_tri).select_related('hang_hoa').order_by('-so_luong'))

    items = []
    dung_luong_da_dung = 0
    for row in ton_rows:
        muc_chiem_cho = max(1, int(getattr(row.hang_hoa, 'muc_chiem_cho', 1) or 1))
        dung_luong_su_dung = int(row.so_luong or 0) * muc_chiem_cho
        dung_luong_da_dung += dung_luong_su_dung
        items.append({
            'ma_hang': row.hang_hoa.ma_hang,
            'ten_hang': row.hang_hoa.ten_hang,
            'so_luong': int(row.so_luong or 0),
            'muc_chiem_cho': muc_chiem_cho,
            'dung_luong_su_dung': dung_luong_su_dung,
        })

    suc_chua_toi_da = int(vi_tri.suc_chua_toi_da or SUC_CHUA_O_MAC_DINH)
    dung_luong_con_lai = max(0, suc_chua_toi_da - dung_luong_da_dung)
    if dung_luong_con_lai <= 0:
        trang_thai = 'DA_DAY'
    elif dung_luong_con_lai <= 10:
        trang_thai = 'GAN_DAY'
    else:
        trang_thai = 'CON_TRONG'

    return JsonResponse({
        'vi_tri_id': vi_tri.id,
        'ma_vi_tri': vi_tri.ma_vi_tri,
        'ten_kho': vi_tri.kho.ten_kho,
        'suc_chua_toi_da': suc_chua_toi_da,
        'dung_luong_da_dung': dung_luong_da_dung,
        'dung_luong_con_lai': dung_luong_con_lai,
        'trang_thai': trang_thai,
        'items': items,
    })


# ─── TỒN KHO ────────────────────────────────────────────────
@login_required
def ton_kho_list(request):
    if not _can_access_inventory(request.user):
        messages.error(request, 'Bạn không có quyền xem tồn kho')
        return redirect('dashboard')

    kho_id = request.GET.get('kho', '').strip()
    q = request.GET.get('q', '').strip()
    ma_hang = request.GET.get('ma_hang', '').strip()
    ten_hang = request.GET.get('ten_hang', '').strip()
    barcode = request.GET.get('barcode', '').strip()
    nhom_hang_id = request.GET.get('nhom_hang', '').strip()
    vi_tri = request.GET.get('vi_tri', '').strip()
    trang_thai_ton = request.GET.get('trang_thai_ton', '').strip()

    items = TonKho.objects.select_related(
        'hang_hoa', 'kho', 'hang_hoa__nhom_hang', 'hang_hoa__don_vi_tinh', 'hang_hoa__thuong_hieu'
    )

    if kho_id:
        items = items.filter(kho_id=kho_id)
    if q:
        items = items.filter(Q(hang_hoa__ma_hang__icontains=q) | Q(hang_hoa__ten_hang__icontains=q))
    if ma_hang:
        items = items.filter(hang_hoa__ma_hang__icontains=ma_hang)
    if ten_hang:
        items = items.filter(hang_hoa__ten_hang__icontains=ten_hang)
    if barcode:
        items = items.filter(Q(hang_hoa__ma_hang__icontains=barcode) | Q(hang_hoa__ten_hang__icontains=barcode))
    if nhom_hang_id:
        items = items.filter(hang_hoa__nhom_hang_id=nhom_hang_id)

    items = list(items.order_by('hang_hoa__ma_hang', 'kho__ma_kho'))

    ton_vitri_qs = TonKhoViTri.objects.select_related('vi_tri').filter(so_luong__gt=0)
    if vi_tri:
        ton_vitri_qs = ton_vitri_qs.filter(vi_tri__ma_vi_tri__icontains=vi_tri)
    vi_tri_map = {}
    for row in ton_vitri_qs:
        key = (row.hang_hoa_id, row.kho_id)
        vi_tri_map.setdefault(key, []).append(row.vi_tri.ma_vi_tri)

    muc_ton_map = {
        (mt.hang_hoa_id, mt.kho_id): mt
        for mt in MucTonKho.objects.select_related('hang_hoa', 'kho')
    }

    filtered_items = []
    for item in items:
        key = (item.hang_hoa_id, item.kho_id)
        vi_tri_list = sorted(set(vi_tri_map.get(key, [])))
        if vi_tri and not vi_tri_list:
            continue

        item.vi_tri_hien_tai = ', '.join(vi_tri_list) if vi_tri_list else '-'
        item.so_luong_loi = int(item.so_luong_loi or 0)
        item.so_luong_thuong = max(0, int(item.so_luong or 0) - item.so_luong_loi)
        item.tong_gia_tri = int((item.so_luong_thuong + item.so_luong_loi) * (item.gia_von_tb or 0))

        muc_ton = muc_ton_map.get(key)
        item.ton_toi_thieu_ap_dung = int(muc_ton.ton_toi_thieu) if muc_ton else int(item.hang_hoa.ton_toi_thieu or 0)
        item.ton_toi_da_ap_dung = int(muc_ton.ton_toi_da) if (muc_ton and muc_ton.ton_toi_da is not None) else int(item.hang_hoa.ton_toi_da or 0)

        tong_ton = int(item.so_luong or 0)
        if tong_ton <= 0:
            item.trang_thai_ton = 'het_hang'
        elif tong_ton <= item.ton_toi_thieu_ap_dung:
            item.trang_thai_ton = 'sap_het'
        elif item.ton_toi_da_ap_dung > 0 and tong_ton > item.ton_toi_da_ap_dung:
            item.trang_thai_ton = 'vuot_toi_da'
        else:
            item.trang_thai_ton = 'binh_thuong'

        if trang_thai_ton and item.trang_thai_ton != trang_thai_ton:
            continue

        filtered_items.append(item)

    tong_gia_tri = sum(i.tong_gia_tri for i in filtered_items)
    so_hang_can_nhap = sum(1 for i in filtered_items if i.trang_thai_ton in ('het_hang', 'sap_het'))
    tong_chung_lo = len(filtered_items)
    so_hang_het = sum(1 for i in filtered_items if i.trang_thai_ton == 'het_hang')
    so_hang_sap_het = sum(1 for i in filtered_items if i.trang_thai_ton == 'sap_het')
    so_hang_vuot_toi_da = sum(1 for i in filtered_items if i.trang_thai_ton == 'vuot_toi_da')
    tong_hang_loi = sum(int(i.so_luong_loi or 0) for i in filtered_items)
    tong_so_luong_ton = sum(int(i.so_luong or 0) for i in filtered_items)
    ty_le_hang_loi = round((tong_hang_loi / tong_so_luong_ton) * 100, 2) if tong_so_luong_ton > 0 else 0
    tong_sku_canh_bao = so_hang_het + so_hang_sap_het + so_hang_vuot_toi_da

    if request.GET.get('export') == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = 'Ton kho'
        ws.append([
            'Mã hàng',
            'Tên hàng',
            'Nhóm hàng',
            'Kho',
            'Vị trí/Kệ',
            'Đơn vị tính',
            'SL hàng thường',
            'SL hàng lỗi',
            'Giá vốn bình quân',
            'Giá trị tồn kho',
            'Trạng thái tồn kho',
        ])

        trang_thai_label = {
            'het_hang': 'Hết hàng',
            'sap_het': 'Sắp hết',
            'vuot_toi_da': 'Vượt tối đa',
            'binh_thuong': 'Bình thường',
        }

        for item in filtered_items:
            ws.append([
                item.hang_hoa.ma_hang,
                item.hang_hoa.ten_hang,
                item.hang_hoa.nhom_hang.ten_nhom if item.hang_hoa.nhom_hang else '',
                item.kho.ten_kho,
                item.vi_tri_hien_tai,
                item.hang_hoa.don_vi_tinh.ten if item.hang_hoa.don_vi_tinh else '',
                int(item.so_luong_thuong or 0),
                int(item.so_luong_loi or 0),
                int(item.gia_von_tb or 0),
                int(item.tong_gia_tri or 0),
                trang_thai_label.get(item.trang_thai_ton, item.trang_thai_ton),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="ton_kho_hien_tai.xlsx"'
        wb.save(response)
        return response

    context = {
        'items': filtered_items,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'nhom_hang_list': HangHoa.objects.exclude(nhom_hang__isnull=True).values('nhom_hang__id', 'nhom_hang__ten_nhom').distinct().order_by('nhom_hang__ten_nhom'),
        'kho_filter': kho_id,
        'q': q,
        'ma_hang': ma_hang,
        'ten_hang': ten_hang,
        'barcode': barcode,
        'nhom_hang_filter': nhom_hang_id,
        'vi_tri_filter': vi_tri,
        'trang_thai_ton_filter': trang_thai_ton,
        'tong_gia_tri': int(tong_gia_tri),
        'so_hang_can_nhap': so_hang_can_nhap,
        'tong_chung_lo': tong_chung_lo,
        'so_hang_het': so_hang_het,
        'so_hang_sap_het': so_hang_sap_het,
        'so_hang_vuot_toi_da': so_hang_vuot_toi_da,
        'tong_hang_loi': tong_hang_loi,
        'tong_so_luong_ton': tong_so_luong_ton,
        'ty_le_hang_loi': ty_le_hang_loi,
        'tong_sku_canh_bao': tong_sku_canh_bao,
        'tong_kho': Kho.objects.filter(trang_thai=True).count(),
        'page_title': 'Tồn kho hiện tại',
        'active_menu': 'ton_kho',
    }
    return render(request, 'kho/ton_kho_list.html', context)


@login_required
def thiet_lap_muc_ton_kho(request):
    if not (request.user.is_superuser or request.user.is_staff or request.user.has_perm('kho.change_tonkho')):
        messages.error(request, 'Bạn không có quyền thiết lập mức tồn kho')
        return redirect('ton_kho_list')

    if request.method != 'POST':
        return redirect('ton_kho_list')

    hang_hoa_id = request.POST.get('hang_hoa_id')
    kho_id = request.POST.get('kho_id')
    ton_toi_thieu = request.POST.get('ton_toi_thieu', '0').strip()
    ton_toi_da = request.POST.get('ton_toi_da', '').strip()
    ghi_chu = request.POST.get('ghi_chu', '').strip()

    if not hang_hoa_id or not kho_id:
        messages.error(request, 'Vui lòng chọn hàng hóa và kho áp dụng')
        return redirect('ton_kho_list')

    try:
        ton_min = int(ton_toi_thieu or '0')
    except ValueError:
        messages.error(request, 'Vui lòng kiểm tra lại thông tin')
        return redirect('ton_kho_list')

    ton_max = None
    if ton_toi_da:
        try:
            ton_max = int(ton_toi_da)
        except ValueError:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin')
            return redirect('ton_kho_list')

    if ton_min < 0:
        messages.error(request, 'Tồn tối thiểu phải lớn hơn hoặc bằng 0')
        return redirect('ton_kho_list')

    if ton_max is not None and ton_max < ton_min:
        messages.error(request, 'Mức tồn tối đa phải lớn hơn hoặc bằng mức tồn tối thiểu')
        return redirect('ton_kho_list')

    MucTonKho.objects.update_or_create(
        hang_hoa_id=hang_hoa_id,
        kho_id=kho_id,
        defaults={
            'ton_toi_thieu': ton_min,
            'ton_toi_da': ton_max,
            'ghi_chu': ghi_chu,
            'nguoi_cap_nhat': request.user,
        }
    )

    messages.success(request, 'Thiết lập mức tồn kho thành công')
    return redirect('ton_kho_list')


# ─── SƠ ĐỒ KHO ──────────────────────────────────────────────
@login_required
def so_do_kho(request):
    kho_sel = request.GET.get('kho_id', '')
    hien_thi = request.GET.get('hien_thi', 'tat_ca')
    if hien_thi not in ('tat_ca', 'co_hang'):
        hien_thi = 'tat_ca'
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

    map_kho_list = [k for k in kho_list if str(k.id) == str(kho_sel)] if kho_sel else kho_list
    kho_maps = []
    ma_pattern = re.compile(r'^(?P<side>[A-Z0-9]+)-D(?P<day>\d+)-K(?P<ke>\d+)-T(?P<tang>\d+)$')
    for kho in map_kho_list:
        vi_tri_list = list(
            ViTriKho.objects.filter(kho=kho).order_by('ma_vi_tri')
        )
        vi_tri_id_map = {(vt.ma_vi_tri or '').upper(): vt.id for vt in vi_tri_list}
        ton_items = list(
            TonKho.objects.select_related('hang_hoa', 'hang_hoa__don_vi_tinh')
            .filter(kho=kho, so_luong__gt=0)
            .order_by('-so_luong', 'hang_hoa__ma_hang')
        )
        tong_so_luong = sum(t.so_luong for t in ton_items)

        structure = {}
        non_standard = []
        for vt in vi_tri_list:
            m = ma_pattern.match((vt.ma_vi_tri or '').upper())
            if not m:
                non_standard.append(vt)
                continue

            side = m.group('side')
            day = int(m.group('day'))
            ke = int(m.group('ke'))
            tang = int(m.group('tang'))

            if side not in structure:
                structure[side] = {}
            if day not in structure[side]:
                structure[side][day] = {}
            if ke not in structure[side][day]:
                structure[side][day][ke] = set()

            structure[side][day][ke].add(tang)

        side_blocks = []
        for side, days in sorted(structure.items(), key=lambda x: x[0]):
            day_blocks = []
            total_kes = 0
            total_positions = 0
            max_tang = 0

            for day, kes in sorted(days.items(), key=lambda x: x[0]):
                ke_blocks = []
                for ke, tangs in sorted(kes.items(), key=lambda x: x[0]):
                    tang_list = [1, 2, 3]
                    tang_count = len(tang_list)
                    ke_blocks.append({
                        'ke': ke,
                        'tang_list': tang_list,
                        'tang_count': tang_count,
                    })
                    max_tang = max(max_tang, tang_count)
                    total_positions += tang_count

                total_kes += len(ke_blocks)
                day_blocks.append({
                    'day': day,
                    'ke_blocks': ke_blocks,
                    'ke_count': len(ke_blocks),
                })

            side_blocks.append({
                'side': side,
                'day_blocks': day_blocks,
                'day_count': len(day_blocks),
                'total_kes': total_kes,
                'total_positions': total_positions,
                'max_tang': max_tang,
            })

        ordered_slots = []
        for side, days in sorted(structure.items(), key=lambda x: x[0]):
            for day, kes in sorted(days.items(), key=lambda x: x[0]):
                for ke, tangs in sorted(kes.items(), key=lambda x: x[0]):
                    for tang in sorted(tangs):
                        ordered_slots.append({
                            'side': side,
                            'day': day,
                            'ke': ke,
                            'tang': tang,
                            'ma_vi_tri': f"{side}-D{day:02d}-K{ke:02d}-T{tang:02d}",
                        })

        ton_vitri_rows = list(
            TonKhoViTri.objects.select_related('vi_tri', 'hang_hoa')
            .filter(kho=kho, so_luong__gt=0)
        )
        ton_by_slot = {(r.vi_tri.ma_vi_tri or '').upper(): r for r in ton_vitri_rows}
        overflow_items = []
        occupied_side_blocks = []

        display_side_blocks = []
        displayed_count = 0
        for side in side_blocks:
            day_blocks = []
            for day in side['day_blocks']:
                ke_blocks = []
                for ke in day['ke_blocks']:
                    levels = []
                    for tang in ke['tang_list']:
                        ma_vi_tri = f"{side['side']}-D{day['day']:02d}-K{ke['ke']:02d}-T{tang:02d}"
                        ma_vi_tri_key = ma_vi_tri.upper()
                        ton = ton_by_slot.get(ma_vi_tri_key)
                        if hien_thi == 'co_hang' and ton is None:
                            continue
                        levels.append({
                            'tang': tang,
                            'ma_vi_tri': ma_vi_tri,
                            'vi_tri_id': vi_tri_id_map.get(ma_vi_tri_key),
                            'ton': ton,
                        })
                        displayed_count += 1

                    # Giữ khung kệ để dãy không bị mất cột khi không có hàng.
                    if levels or hien_thi == 'tat_ca':
                        ke_blocks.append({
                            'ke': ke['ke'],
                            'levels': levels,
                        })

                # Luôn giữ đủ các dãy để sơ đồ không bị dồn sang 1 dãy.
                day_blocks.append({
                    'day': day['day'],
                    'ke_blocks': ke_blocks,
                })

            display_side_blocks.append({
                'side': side['side'],
                'day_blocks': day_blocks,
            })

        kho_maps.append({
            'kho': kho,
            'vi_tri_list': vi_tri_list,
            'ton_items': ton_items[:12],
            'ton_items_total': len(ton_items),
            'tong_so_luong': tong_so_luong,
            'side_blocks': side_blocks,
            'occupied_side_blocks': occupied_side_blocks,
            'display_side_blocks': display_side_blocks,
            'displayed_count': displayed_count,
            'occupied_count': len(ton_vitri_rows),
            'total_slot_count': len(ordered_slots),
            'overflow_items': overflow_items,
            'non_standard': non_standard,
        })

    return render(request, 'kho/so_do_kho.html', {
        'kho_list': kho_list,
        'items': items,
        'kho_maps': kho_maps,
        'kho_sel': kho_sel,
        'hien_thi': hien_thi,
        'page_title': 'Sơ đồ kho',
        'active_menu': 'so_do_kho',
    })


# ─── TÍNH GIÁ XUẤT KHO ──────────────────────────────────────
@login_required
def tinh_gia_xuat(request):
    if not _can_access_inventory(request.user):
        messages.error(request, 'Bạn không có quyền tính giá xuất kho')
        return redirect('dashboard')

    kho_filter = request.GET.get('kho', '')
    hang_filter = request.GET.get('hang_hoa', '')

    if request.method == 'POST':
        kho_filter = request.POST.get('kho', '').strip()
        hang_filter = request.POST.get('hang_hoa', '').strip()
        with transaction.atomic():
            ok, errors, updated = _recalculate_weighted_average(
                kho_id=kho_filter or None,
                hang_hoa_id=hang_filter or None,
            )
            if not ok:
                messages.error(request, 'Không thể tính giá do tồn kho âm')
                for err in errors[:5]:
                    hang = HangHoa.objects.filter(pk=err['hang_hoa_id']).first()
                    kho = Kho.objects.filter(pk=err['kho_id']).first()
                    messages.error(
                        request,
                        f"{hang.ma_hang if hang else err['hang_hoa_id']} - {kho.ma_kho if kho else err['kho_id']}: "
                        f"xuất {err['so_luong_xuat']} > tồn {err['so_luong_hien_co']}"
                    )
            elif updated == 0:
                messages.warning(request, 'Không có dữ liệu để tính giá xuất kho')
            else:
                messages.success(request, f'Tính giá bình quân xuất kho thành công ({updated} tồn kho đã cập nhật)')

    items = TonKho.objects.select_related(
        'hang_hoa', 'kho', 'hang_hoa__nhom_hang', 'hang_hoa__don_vi_tinh'
    ).order_by('hang_hoa__ma_hang')

    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    if hang_filter:
        items = items.filter(hang_hoa_id=hang_filter)

    tong_gia_tri_ton = sum(t.so_luong * t.gia_von_tb for t in items)
    thang = timezone.now().strftime('%m/%Y')

    # Thống kê xuất kho tháng này
    now = timezone.now()
    first_day = now.replace(day=1)
    tong_phieu_xuat = PhieuXuat.objects.filter(
        ngay_chung_tu__gte=first_day.date(), trang_thai__in=('2', '3')
    ).count()
    tong_gia_von_xuat = PhieuXuat.objects.filter(
        ngay_chung_tu__gte=first_day.date(), trang_thai__in=('2', '3')
    ).aggregate(t=Sum('tong_gia_von'))['t'] or 0

    return render(request, 'kho/tinh_gia_xuat.html', {
        'items': items,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_hoa_list': HangHoa.objects.filter(trang_thai='dang_ban').order_by('ma_hang')[:500],
        'kho_filter': kho_filter,
        'hang_filter': hang_filter,
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
        ngay_chung_tu__range=[tu_ngay, den_ngay],
        trang_thai__in=('2', '3')
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
            phieu_xuat__ngay_chung_tu__range=[tu_ngay, den_ngay],
            phieu_xuat__trang_thai__in=('2', '3'),
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
    kho_filter = request.GET.get('kho', '')
    trang_thai_filter = request.GET.get('trang_thai', '')
    items = PhieuNhap.objects.select_related('nha_cung_cap', 'kho')
    if q:
        items = items.filter(Q(so_phieu__icontains=q) |
                             Q(nha_cung_cap__ten_ncc__icontains=q))
    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    if trang_thai_filter in ('1', '2', '3'):
        items = items.filter(trang_thai=trang_thai_filter)
    context = {
        'items': items[:50],
        'q': q,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_filter,
        'trang_thai_filter': trang_thai_filter,
        'page_title': 'Phiếu nhập kho',
        'active_menu': 'phieu_nhap',
    }
    return render(request, 'kho/phieu_nhap_list.html', context)


@login_required
def phieu_nhap_them(request):
    if request.method == 'POST':
        data = request.POST
        kho_id = data.get('kho')
        loai_nhap = _normalize_loai_nhap(data.get('loai_nhap', '1'))
        trang_thai_mong_muon = str(data.get('trang_thai', '1') or '1').strip()
        if trang_thai_mong_muon not in ('1', '2', '3'):
            trang_thai_mong_muon = '1'
        ncc_id = data.get('ncc') or None
        if not kho_id:
            messages.error(request, 'Vui lòng chọn kho nhận')
            return redirect('phieu_nhap_them')

        if loai_nhap == '1' and not ncc_id:
            messages.error(request, 'Loại chứng từ 1 - Mua nhà cung cấp bắt buộc chọn Nhà cung cấp')
            return redirect('phieu_nhap_them')

        so_phieu = data.get('so_phieu') or _gen_so_phieu('NK')
        ngay_ct = data.get('ngay_chung_tu') or data.get('ngay_nhap') or date.today()
        phieu = PhieuNhap.objects.create(
            so_phieu=so_phieu,
            ngay_chung_tu=ngay_ct,
            ngay_nhap=ngay_ct,
            loai_nhap=loai_nhap,
            trang_thai='1',
            nha_cung_cap_id=ncc_id,
            so_hd_ncc=data.get('so_hd_ncc', ''),
            ngay_hd_ncc=data.get('ngay_hd_ncc') or None,
            kho_id=kho_id,
            ghi_chu=data.get('ghi_chu', ''),
            nguoi_tao=request.user,
        )

        # Xử lý chi tiết
        hang_ids = data.getlist('hang_id[]')
        sl_nhans = data.getlist('so_luong_nhan[]')
        don_gias = data.getlist('don_gia[]')
        tk_nos = data.getlist('tk_no[]')
        tk_cos = data.getlist('tk_co[]')
        so_dong_hop_le = 0

        for i in range(len(hang_ids)):
            if hang_ids[i] and sl_nhans[i] and don_gias[i]:
                try:
                    sl_nhan = int(sl_nhans[i])
                    don_gia = float(don_gias[i])
                except (ValueError, TypeError):
                    continue

                if sl_nhan <= 0 or don_gia < 0:
                    continue

                tk_no = tk_nos[i].strip() if i < len(tk_nos) else ''
                tk_co = tk_cos[i].strip() if i < len(tk_cos) else ''

                PhieuNhap_CT.objects.create(
                    phieu_nhap=phieu,
                    hang_hoa_id=hang_ids[i],
                    so_luong_nhan=sl_nhan,
                    don_gia=don_gia,
                    thue_vat=0,
                    tk_no=tk_no,
                    tk_co=tk_co,
                )
                so_dong_hop_le += 1

        if so_dong_hop_le == 0:
            phieu.delete()
            messages.error(request, 'Phiếu nhập phải có ít nhất 1 dòng hàng hóa hợp lệ')
            return redirect('phieu_nhap_them')

        phieu.tinh_tong()

        thong_diep = [f'Đã tạo phiếu nhập {phieu.so_phieu} ở bước 1 - Lập phiếu']

        if trang_thai_mong_muon == '2':
            ok = phieu.xac_nhan_nhap_kho()
            if ok:
                so_dong_phan_bo = _ghi_nhan_phan_bo_vi_tri(phieu)
                thong_diep.append(f'Đã tự động chuyển bước 2 - Sổ kho ({so_dong_phan_bo} dòng vị trí)')
            else:
                messages.error(request, 'Không thể tự động chuyển sang bước 2 - Sổ kho')
                return redirect('phieu_nhap_detail', pk=phieu.pk)

        if trang_thai_mong_muon == '3':
            ok = phieu.xac_nhan_nhap_kho()
            if not ok:
                messages.error(request, 'Không thể tự động chuyển sang bước 2 - Sổ kho để chuyển sổ cái')
                return redirect('phieu_nhap_detail', pk=phieu.pk)

            so_dong_phan_bo = _ghi_nhan_phan_bo_vi_tri(phieu)
            phieu.trang_thai = '3'
            phieu.save(update_fields=['trang_thai'])
            thong_diep.append(f'Đã tự động chuyển bước 2 - Sổ kho ({so_dong_phan_bo} dòng vị trí)')
            thong_diep.append('Đã tự động chuyển bước 3 - Sổ cái')

        messages.success(request, '. '.join(thong_diep))
        return redirect('phieu_nhap_detail', pk=phieu.pk)

    copy_from = request.GET.get('copy_from', '').strip()
    copy_data = None
    if copy_from:
        source = get_object_or_404(
            PhieuNhap.objects.select_related('nha_cung_cap', 'kho').prefetch_related('chi_tiet__hang_hoa'),
            pk=copy_from,
        )
        copy_data = {
            'ngay_chung_tu': source.ngay_chung_tu.isoformat(),
            'loai_nhap': source.loai_nhap,
            'kho_id': str(source.kho_id or ''),
            'ncc_id': str(source.nha_cung_cap_id or ''),
            'ncc_label': f'{source.nha_cung_cap.ma_ncc} - {source.nha_cung_cap.ten_ncc}' if source.nha_cung_cap else '',
            'so_hd_ncc': source.so_hd_ncc or '',
            'ngay_hd_ncc': source.ngay_hd_ncc.isoformat() if source.ngay_hd_ncc else '',
            'ghi_chu': source.ghi_chu or '',
            'rows': [
                {
                    'hang_id': str(ct.hang_hoa_id),
                    'hang_label': f'{ct.hang_hoa.ma_hang} - {ct.hang_hoa.ten_hang}',
                    'so_luong_nhan': int(ct.so_luong_nhan or 0),
                    'don_gia': float(ct.don_gia or 0),
                    'tk_no': ct.tk_no or '',
                    'tk_co': ct.tk_co or '',
                }
                for ct in source.chi_tiet.all()
            ],
        }

    ma_ncc_hop_le = KhachHang.objects.filter(trang_thai=True, la_nha_cung_cap=True).values_list('ma_kh', flat=True)
    context = {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'ncc_list': NhaCungCap.objects.filter(trang_thai=True, ma_ncc__in=ma_ncc_hop_le).order_by('ma_ncc'),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'tai_khoan_list': TaiKhoanKeToan.objects.filter(trang_thai=True).order_by('ma_tk'),
        'so_phieu_default': _gen_so_phieu('NK'),
        'today': date.today(),
        'copy_data': copy_data,
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
@transaction.atomic
def phieu_nhap_sua(request, pk):
    phieu = get_object_or_404(PhieuNhap.objects.select_related('nha_cung_cap', 'kho').prefetch_related('chi_tiet__hang_hoa'), pk=pk)

    if request.method == 'POST':
        ok, err_msg = _rollback_phieu_nhap_inventory(phieu)
        if not ok:
            messages.error(request, err_msg)
            return redirect('phieu_nhap_detail', pk=pk)

        data = request.POST
        kho_id = data.get('kho')
        loai_nhap = _normalize_loai_nhap(data.get('loai_nhap', '1'))
        trang_thai_mong_muon = str(data.get('trang_thai', '1') or '1').strip()
        if trang_thai_mong_muon not in ('1', '2', '3'):
            trang_thai_mong_muon = '1'
        ncc_id = data.get('ncc') or None

        if not kho_id:
            messages.error(request, 'Vui lòng chọn kho nhận')
            return redirect('phieu_nhap_sua', pk=pk)
        if loai_nhap == '1' and not ncc_id:
            messages.error(request, 'Loại chứng từ 1 - Mua nhà cung cấp bắt buộc chọn Nhà cung cấp')
            return redirect('phieu_nhap_sua', pk=pk)

        phieu.ngay_chung_tu = data.get('ngay_chung_tu') or date.today()
        phieu.ngay_nhap = phieu.ngay_chung_tu
        phieu.loai_nhap = loai_nhap
        phieu.nha_cung_cap_id = ncc_id
        phieu.so_hd_ncc = data.get('so_hd_ncc', '')
        phieu.ngay_hd_ncc = data.get('ngay_hd_ncc') or None
        phieu.kho_id = kho_id
        phieu.ghi_chu = data.get('ghi_chu', '')
        phieu.trang_thai = '1'
        phieu.save(update_fields=['ngay_chung_tu', 'ngay_nhap', 'loai_nhap', 'nha_cung_cap', 'so_hd_ncc', 'ngay_hd_ncc', 'kho', 'ghi_chu', 'trang_thai'])

        phieu.chi_tiet.all().delete()
        hang_ids = data.getlist('hang_id[]')
        sl_nhans = data.getlist('so_luong_nhan[]')
        don_gias = data.getlist('don_gia[]')
        tk_nos = data.getlist('tk_no[]')
        tk_cos = data.getlist('tk_co[]')
        so_dong_hop_le = 0

        for i in range(len(hang_ids)):
            if hang_ids[i] and sl_nhans[i] and don_gias[i]:
                try:
                    sl_nhan = int(sl_nhans[i])
                    don_gia = float(don_gias[i])
                except (ValueError, TypeError):
                    continue
                if sl_nhan <= 0 or don_gia < 0:
                    continue
                tk_no = tk_nos[i].strip() if i < len(tk_nos) else ''
                tk_co = tk_cos[i].strip() if i < len(tk_cos) else ''
                PhieuNhap_CT.objects.create(
                    phieu_nhap=phieu,
                    hang_hoa_id=hang_ids[i],
                    so_luong_nhan=sl_nhan,
                    don_gia=don_gia,
                    thue_vat=0,
                    tk_no=tk_no,
                    tk_co=tk_co,
                )
                so_dong_hop_le += 1

        if so_dong_hop_le == 0:
            messages.error(request, 'Phiếu nhập phải có ít nhất 1 dòng hàng hóa hợp lệ')
            return redirect('phieu_nhap_sua', pk=pk)

        phieu.tinh_tong()
        if trang_thai_mong_muon == '2':
            phieu.xac_nhan_nhap_kho()
            _ghi_nhan_phan_bo_vi_tri(phieu)
        if trang_thai_mong_muon == '3':
            ok = phieu.xac_nhan_nhap_kho()
            if ok:
                _ghi_nhan_phan_bo_vi_tri(phieu)
                phieu.trang_thai = '3'
                phieu.save(update_fields=['trang_thai'])

        messages.success(request, f'Đã cập nhật phiếu nhập {phieu.so_phieu}')
        return redirect('phieu_nhap_detail', pk=pk)

    copy_data = {
        'ngay_chung_tu': phieu.ngay_chung_tu.isoformat(),
        'loai_nhap': phieu.loai_nhap,
        'kho_id': str(phieu.kho_id or ''),
        'ncc_id': str(phieu.nha_cung_cap_id or ''),
        'ncc_label': f'{phieu.nha_cung_cap.ma_ncc} - {phieu.nha_cung_cap.ten_ncc}' if phieu.nha_cung_cap else '',
        'so_hd_ncc': phieu.so_hd_ncc or '',
        'ngay_hd_ncc': phieu.ngay_hd_ncc.isoformat() if phieu.ngay_hd_ncc else '',
        'ghi_chu': phieu.ghi_chu or '',
        'rows': [
            {
                'hang_id': str(ct.hang_hoa_id),
                'hang_label': f'{ct.hang_hoa.ma_hang} - {ct.hang_hoa.ten_hang}',
                'so_luong_nhan': int(ct.so_luong_nhan or 0),
                'don_gia': float(ct.don_gia or 0),
                'tk_no': ct.tk_no or '',
                'tk_co': ct.tk_co or '',
            }
            for ct in phieu.chi_tiet.all()
        ],
    }
    ma_ncc_hop_le = KhachHang.objects.filter(trang_thai=True, la_nha_cung_cap=True).values_list('ma_kh', flat=True)
    return render(request, 'kho/phieu_nhap_form.html', {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'ncc_list': NhaCungCap.objects.filter(trang_thai=True, ma_ncc__in=ma_ncc_hop_le).order_by('ma_ncc'),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'tai_khoan_list': TaiKhoanKeToan.objects.filter(trang_thai=True).order_by('ma_tk'),
        'so_phieu_default': phieu.so_phieu,
        'today': phieu.ngay_chung_tu,
        'copy_data': copy_data,
        'editing_phieu': phieu,
        'page_title': f'Sửa phiếu nhập {phieu.so_phieu}',
        'active_menu': 'phieu_nhap',
    })


@login_required
@transaction.atomic
def phieu_nhap_xoa(request, pk):
    phieu = get_object_or_404(PhieuNhap, pk=pk)
    if request.method != 'POST':
        return redirect('phieu_nhap_list')

    ok, err_msg = _rollback_phieu_nhap_inventory(phieu)
    if not ok:
        messages.error(request, err_msg)
        return redirect('phieu_nhap_list')

    so_phieu = phieu.so_phieu
    phieu.delete()
    messages.success(request, f'Đã xóa phiếu nhập {so_phieu}')
    return redirect('phieu_nhap_list')


@login_required
@xframe_options_exempt
def phieu_nhap_in(request, pk):
    phieu = get_object_or_404(PhieuNhap.objects.select_related('nha_cung_cap', 'kho', 'nguoi_tao'), pk=pk)
    chi_tiet = list(phieu.chi_tiet.select_related('hang_hoa', 'hang_hoa__don_vi_tinh').all())
    while len(chi_tiet) < 10:
        chi_tiet.append(None)
    return render(request, 'kho/phieu_nhap_print.html', {
        'phieu': phieu,
        'chi_tiet': chi_tiet,
        'page_title': f'In phiếu nhập {phieu.so_phieu}',
        'active_menu': 'phieu_nhap',
    })


@login_required
def phieu_nhap_xac_nhan(request, pk):
    phieu = get_object_or_404(PhieuNhap, pk=pk)
    if request.method == 'POST':
        ok = phieu.xac_nhan_nhap_kho()
        if ok:
            so_dong_phan_bo = _ghi_nhan_phan_bo_vi_tri(phieu)
            messages.success(request, f'Đã ghi Sổ kho thành công: {phieu.so_phieu}. Đã gợi ý/ghi nhận {so_dong_phan_bo} dòng vị trí.')
        else:
            messages.error(request, 'Không thể xác nhận - phiếu đã được xử lý')
    return redirect('phieu_nhap_detail', pk=pk)


@login_required
def phieu_nhap_chuyen_so_cai(request, pk):
    phieu = get_object_or_404(PhieuNhap, pk=pk)
    if request.method == 'POST':
        if phieu.trang_thai == '2':
            phieu.trang_thai = '3'
            phieu.save(update_fields=['trang_thai'])
            messages.success(request, f'Đã chuyển phiếu {phieu.so_phieu} sang bước Sổ cái')
        else:
            messages.error(request, 'Chỉ có thể chuyển Sổ cái sau khi đã ghi Sổ kho (bước 2)')
    return redirect('phieu_nhap_detail', pk=pk)


# ─── PHIẾU XUẤT KHO ────────────────────────────────────────
@login_required
def phieu_xuat_list(request):
    q = request.GET.get('q', '')
    kho_filter = request.GET.get('kho', '')
    trang_thai_filter = request.GET.get('trang_thai', '')
    items = PhieuXuat.objects.select_related('kho')
    if q:
        items = items.filter(so_phieu__icontains=q)
    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    if trang_thai_filter in ('1', '2', '3'):
        items = items.filter(trang_thai=trang_thai_filter)
    context = {
        'items': items[:50],
        'q': q,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_filter,
        'trang_thai_filter': trang_thai_filter,
        'page_title': 'Phiếu xuất kho',
        'active_menu': 'phieu_xuat',
    }
    return render(request, 'kho/phieu_xuat_list.html', context)


@login_required
def phieu_xuat_them(request):
    if request.method == 'POST':
        data = request.POST
        kho_id = data.get('kho')
        trang_thai_mong_muon = str(data.get('trang_thai', '1') or '1').strip()
        if trang_thai_mong_muon not in ('1', '2', '3'):
            trang_thai_mong_muon = '1'
        ngay_ct = data.get('ngay_chung_tu') or data.get('ngay_xuat') or date.today()
        so_phieu_input = (data.get('so_phieu') or '').strip()
        so_phieu_candidate = so_phieu_input if so_phieu_input else _gen_so_phieu('XK')
        if PhieuXuat.objects.filter(so_phieu=so_phieu_candidate).exists():
            so_phieu_candidate = _gen_so_phieu('XK')

        phieu = None
        for _ in range(5):
            try:
                phieu = PhieuXuat.objects.create(
                    so_phieu=so_phieu_candidate,
                    ngay_chung_tu=ngay_ct,
                    ngay_xuat=ngay_ct,
                    loai_xuat=data.get('loai_xuat', 'noi_bo'),
                    kho_id=kho_id,
                    trang_thai='1',
                    nguoi_tao=request.user,
                    ghi_chu=data.get('ghi_chu', ''),
                )
                break
            except IntegrityError:
                so_phieu_candidate = _gen_so_phieu('XK')

        if phieu is None:
            messages.error(request, 'Không thể tạo số phiếu mới, vui lòng thử lại.')
            return redirect('phieu_xuat_them')
        hang_ids = data.getlist('hang_id[]')
        so_luongs = data.getlist('so_luong[]')
        tk_nos = data.getlist('tk_no[]')
        tk_cos = data.getlist('tk_co[]')
        tong_gv = 0
        for i in range(len(hang_ids)):
            if hang_ids[i] and so_luongs[i]:
                h_id = int(hang_ids[i])
                sl = int(so_luongs[i])
                tk = TonKho.objects.filter(hang_hoa_id=h_id, kho_id=kho_id).first()
                gv = tk.gia_von_tb if tk else 0
                tgv = gv * sl
                tk_no = tk_nos[i].strip() if i < len(tk_nos) else ''
                tk_co = tk_cos[i].strip() if i < len(tk_cos) else ''
                PhieuXuat_CT.objects.create(
                    phieu_xuat=phieu, hang_hoa_id=h_id,
                    so_luong=sl, gia_von=gv, tong_gia_von=tgv,
                    tk_no=tk_no, tk_co=tk_co,
                )
                tong_gv += tgv
        phieu.tong_gia_von = tong_gv
        phieu.save(update_fields=['tong_gia_von'])

        thong_diep = [f'Đã tạo phiếu xuất {phieu.so_phieu} ở bước 1 - Lập phiếu']

        if trang_thai_mong_muon in ('2', '3'):
            ok, err_msg = _xac_nhan_phieu_xuat(phieu)
            if not ok:
                messages.error(request, err_msg)
                return redirect('phieu_xuat_detail', pk=phieu.pk)
            thong_diep.append('Đã tự động chuyển bước 2 - Sổ kho')

        if trang_thai_mong_muon == '3':
            phieu.trang_thai = '3'
            phieu.save(update_fields=['trang_thai'])
            thong_diep.append('Đã tự động chuyển bước 3 - Sổ cái')

        messages.success(request, '. '.join(thong_diep))
        return redirect('phieu_xuat_detail', pk=phieu.pk)

    copy_from = request.GET.get('copy_from', '').strip()
    copy_data = None
    if copy_from:
        source = get_object_or_404(
            PhieuXuat.objects.select_related('kho').prefetch_related('chi_tiet__hang_hoa'),
            pk=copy_from,
        )
        copy_data = {
            'ngay_chung_tu': source.ngay_chung_tu.isoformat(),
            'loai_xuat': source.loai_xuat,
            'kho_id': str(source.kho_id or ''),
            'trang_thai': source.trang_thai,
            'ghi_chu': source.ghi_chu or '',
            'rows': [
                {
                    'hang_id': str(ct.hang_hoa_id),
                    'hang_label': f'{ct.hang_hoa.ma_hang} - {ct.hang_hoa.ten_hang}',
                    'so_luong': int(ct.so_luong or 0),
                    'tk_no': ct.tk_no or '',
                    'tk_co': ct.tk_co or '',
                }
                for ct in source.chi_tiet.all()
            ],
        }

    context = {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'so_phieu_default': _gen_so_phieu('XK'),
        'today': date.today(),
        'copy_data': copy_data,
        'page_title': 'Tạo phiếu xuất kho',
        'active_menu': 'phieu_xuat',
    }
    return render(request, 'kho/phieu_xuat_form.html', context)


@login_required
def phieu_xuat_detail(request, pk):
    phieu = get_object_or_404(PhieuXuat, pk=pk)
    chi_tiet = phieu.chi_tiet.select_related('hang_hoa')
    context = {
        'phieu': phieu,
        'chi_tiet': chi_tiet,
        'page_title': f'Phiếu xuất {phieu.so_phieu}',
        'active_menu': 'phieu_xuat',
    }
    return render(request, 'kho/phieu_xuat_detail.html', context)


@login_required
@transaction.atomic
def phieu_xuat_sua(request, pk):
    phieu = get_object_or_404(PhieuXuat.objects.select_related('kho').prefetch_related('chi_tiet__hang_hoa'), pk=pk)

    if request.method == 'POST':
        if _phieu_xuat_has_related_documents(phieu):
            messages.error(request, f'Phiếu {phieu.so_phieu} đã phát sinh chứng từ bán hàng liên quan, không thể sửa/xóa.')
            return redirect('phieu_xuat_detail', pk=pk)

        ok, err_msg = _rollback_phieu_xuat_inventory(phieu)
        if not ok:
            messages.error(request, err_msg)
            return redirect('phieu_xuat_detail', pk=pk)

        data = request.POST
        trang_thai_mong_muon = str(data.get('trang_thai', '1') or '1').strip()
        if trang_thai_mong_muon not in ('1', '2', '3'):
            trang_thai_mong_muon = '1'
        phieu.ngay_chung_tu = data.get('ngay_chung_tu') or date.today()
        phieu.ngay_xuat = phieu.ngay_chung_tu
        phieu.loai_xuat = data.get('loai_xuat', 'noi_bo')
        phieu.kho_id = data.get('kho')
        phieu.ghi_chu = data.get('ghi_chu', '')
        phieu.trang_thai = '1'
        phieu.save(update_fields=['ngay_chung_tu', 'ngay_xuat', 'loai_xuat', 'kho', 'ghi_chu', 'trang_thai'])

        phieu.chi_tiet.all().delete()
        hang_ids = data.getlist('hang_id[]')
        so_luongs = data.getlist('so_luong[]')
        tk_nos = data.getlist('tk_no[]')
        tk_cos = data.getlist('tk_co[]')
        tong_gv = 0
        so_dong_hop_le = 0
        for i in range(len(hang_ids)):
            if hang_ids[i] and so_luongs[i]:
                try:
                    h_id = int(hang_ids[i])
                    sl = int(so_luongs[i])
                except (ValueError, TypeError):
                    continue
                if sl <= 0:
                    continue
                tk = TonKho.objects.filter(hang_hoa_id=h_id, kho_id=phieu.kho_id).first()
                gv = tk.gia_von_tb if tk else 0
                tgv = gv * sl
                tk_no = tk_nos[i].strip() if i < len(tk_nos) else ''
                tk_co = tk_cos[i].strip() if i < len(tk_cos) else ''
                PhieuXuat_CT.objects.create(
                    phieu_xuat=phieu,
                    hang_hoa_id=h_id,
                    so_luong=sl,
                    gia_von=gv,
                    tong_gia_von=tgv,
                    tk_no=tk_no,
                    tk_co=tk_co,
                )
                tong_gv += tgv
                so_dong_hop_le += 1

        if so_dong_hop_le == 0:
            messages.error(request, 'Phiếu xuất phải có ít nhất 1 dòng hàng hóa hợp lệ')
            return redirect('phieu_xuat_sua', pk=pk)

        phieu.tong_gia_von = tong_gv
        phieu.save(update_fields=['tong_gia_von'])

        thong_diep = [f'Đã cập nhật phiếu xuất {phieu.so_phieu} ở bước 1 - Lập phiếu']

        if trang_thai_mong_muon in ('2', '3'):
            ok, err_msg = _xac_nhan_phieu_xuat(phieu)
            if not ok:
                messages.error(request, err_msg)
                return redirect('phieu_xuat_detail', pk=pk)
            thong_diep.append('Đã tự động chuyển bước 2 - Sổ kho')

        if trang_thai_mong_muon == '3':
            phieu.trang_thai = '3'
            phieu.save(update_fields=['trang_thai'])
            thong_diep.append('Đã tự động chuyển bước 3 - Sổ cái')

        messages.success(request, '. '.join(thong_diep))
        return redirect('phieu_xuat_detail', pk=pk)

    copy_data = {
        'ngay_chung_tu': phieu.ngay_chung_tu.isoformat(),
        'loai_xuat': phieu.loai_xuat,
        'kho_id': str(phieu.kho_id or ''),
        'trang_thai': phieu.trang_thai,
        'ghi_chu': phieu.ghi_chu or '',
        'rows': [
            {
                'hang_id': str(ct.hang_hoa_id),
                'hang_label': f'{ct.hang_hoa.ma_hang} - {ct.hang_hoa.ten_hang}',
                'so_luong': int(ct.so_luong or 0),
                'tk_no': ct.tk_no or '',
                'tk_co': ct.tk_co or '',
            }
            for ct in phieu.chi_tiet.all()
        ],
    }
    return render(request, 'kho/phieu_xuat_form.html', {
        'kho_list': Kho.objects.filter(trang_thai=True),
        'hang_list': HangHoa.objects.filter(trang_thai='dang_ban'),
        'so_phieu_default': phieu.so_phieu,
        'today': phieu.ngay_chung_tu,
        'copy_data': copy_data,
        'editing_phieu': phieu,
        'page_title': f'Sửa phiếu xuất {phieu.so_phieu}',
        'active_menu': 'phieu_xuat',
    })


@login_required
@transaction.atomic
def phieu_xuat_xoa(request, pk):
    phieu = get_object_or_404(PhieuXuat, pk=pk)
    if request.method != 'POST':
        return redirect('phieu_xuat_list')

    if _phieu_xuat_has_related_documents(phieu):
        messages.error(request, f'Phiếu {phieu.so_phieu} đã phát sinh chứng từ bán hàng liên quan, không thể sửa/xóa.')
        return redirect('phieu_xuat_list')

    ok, err_msg = _rollback_phieu_xuat_inventory(phieu)
    if not ok:
        messages.error(request, err_msg)
        return redirect('phieu_xuat_list')

    so_phieu = phieu.so_phieu
    phieu.delete()
    messages.success(request, f'Đã xóa phiếu xuất {so_phieu}')
    return redirect('phieu_xuat_list')


@login_required
@transaction.atomic
def phieu_xuat_xac_nhan(request, pk):
    phieu = get_object_or_404(PhieuXuat, pk=pk)
    if request.method == 'POST':
        ok, err_msg = _xac_nhan_phieu_xuat(phieu)
        if ok:
            messages.success(request, f'Đã ghi Sổ kho thành công: {phieu.so_phieu}')
        else:
            messages.error(request, err_msg)

    return redirect('phieu_xuat_detail', pk=pk)


@login_required
def phieu_xuat_chuyen_so_cai(request, pk):
    phieu = get_object_or_404(PhieuXuat, pk=pk)
    if request.method == 'POST':
        if phieu.trang_thai == '2':
            phieu.trang_thai = '3'
            phieu.save(update_fields=['trang_thai'])
            messages.success(request, f'Đã chuyển phiếu {phieu.so_phieu} sang bước Sổ cái')
        else:
            messages.error(request, 'Chỉ có thể chuyển Sổ cái sau khi đã ghi Sổ kho (bước 2)')
    return redirect('phieu_xuat_detail', pk=pk)


# ─── KIỂM KÊ ────────────────────────────────────────────────
# ─── XUẤT/NHẬP KHO (EXCEL) ─────────────────────────────────
@login_required
def phieu_xuat_export_data(request):
    """Export phiếu xuất hiện tại sang Excel"""
    items = PhieuXuat.objects.select_related('kho').all()
    
    kho_filter = request.GET.get('kho', '').strip()
    trang_thai_filter = request.GET.get('trang_thai', '').strip()
    
    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    if trang_thai_filter:
        items = items.filter(trang_thai=trang_thai_filter)
    
    wb = Workbook()
    ws = wb.active
    ws.title = 'Phieu Xuat'
    ws.append(['Số phiếu', 'Ngày xuất', 'Kho', 'Loại xuất', 'Số lượng', 'Tổng giá vốn', 'Trạng thái'])
    
    for item in items:
        ws.append([
            item.so_phieu,
            item.ngay_chung_tu.strftime('%d/%m/%Y') if item.ngay_chung_tu else '',
            item.kho.ten_kho if item.kho else '',
            item.loai_xuat,
            item.chi_tiet.count(),
            int(item.tong_gia_von or 0),
            item.get_trang_thai_display() if hasattr(item, 'get_trang_thai_display') else item.trang_thai,
        ])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="phieu_xuat.xlsx"'
    wb.save(response)
    return response


@login_required
def phieu_xuat_export_template(request):
    """Xuất template phiếu xuất"""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Phieu Xuat'
    ws.append(['Ngày xuất', 'Mã kho', 'Mã hàng', 'Số lượng', 'Ghi chú'])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_phieu_xuat.xlsx"'
    wb.save(response)
    return response


@login_required
def phieu_xuat_import_excel(request):
    """Import phiếu xuất từ Excel"""
    if request.method != 'POST':
        messages.error(request, 'Phương thức không được hỗ trợ')
        return redirect('phieu_xuat_list')
    
    file = request.FILES.get('file')
    if not file:
        messages.error(request, 'Vui lòng chọn file Excel')
        return redirect('phieu_xuat_list')
    
    messages.success(request, 'Chức năng import phiếu xuất sẽ được phát triển. Hiện tại vui lòng tạo phiếu thủ công.')
    return redirect('phieu_xuat_list')


@login_required
def phieu_nhap_export_data(request):
    """Export phiếu nhập hiện tại sang Excel"""
    items = PhieuNhap.objects.select_related('kho', 'nha_cung_cap').all()
    
    kho_filter = request.GET.get('kho', '').strip()
    trang_thai_filter = request.GET.get('trang_thai', '').strip()
    
    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    if trang_thai_filter:
        items = items.filter(trang_thai=trang_thai_filter)
    
    wb = Workbook()
    ws = wb.active
    ws.title = 'Phieu Nhap'
    ws.append(['Số phiếu', 'Ngày nhập', 'Kho', 'Loại nhập', 'Nhà cung cấp', 'Số lượng', 'Tổng tiền', 'Trạng thái'])
    
    for item in items:
        ws.append([
            item.so_phieu,
            item.ngay_chung_tu.strftime('%d/%m/%Y') if item.ngay_chung_tu else '',
            item.kho.ten_kho if item.kho else '',
            item.loai_nhap,
            item.nha_cung_cap.ten_ncc if item.nha_cung_cap else '',
            item.chi_tiet.count(),
            int(item.tong_tien or 0),
            item.get_trang_thai_display() if hasattr(item, 'get_trang_thai_display') else item.trang_thai,
        ])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="phieu_nhap.xlsx"'
    wb.save(response)
    return response


@login_required
def phieu_nhap_export_template(request):
    """Xuất template phiếu nhập"""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Phieu Nhap'
    ws.append(['Ngày nhập', 'Mã kho', 'Mã NCC', 'Mã hàng', 'Số lượng', 'Đơn giá', 'Ghi chú'])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_phieu_nhap.xlsx"'
    wb.save(response)
    return response


@login_required
def phieu_nhap_import_excel(request):
    """Import phiếu nhập từ Excel"""
    if request.method != 'POST':
        messages.error(request, 'Phương thức không được hỗ trợ')
        return redirect('phieu_nhap_list')
    
    file = request.FILES.get('file')
    if not file:
        messages.error(request, 'Vui lòng chọn file Excel')
        return redirect('phieu_nhap_list')
    
    messages.success(request, 'Chức năng import phiếu nhập sẽ được phát triển. Hiện tại vui lòng tạo phiếu thủ công.')
    return redirect('phieu_nhap_list')


# ─── KIỂM KÊ ────────────────────────────────────────────────
@login_required
def kiem_ke_list(request):
    q = request.GET.get('q', '').strip()
    kho_filter = request.GET.get('kho', '').strip()
    items = KiemKe.objects.select_related('kho').order_by('-ngay_kiem_ke')
    if q:
        items = items.filter(Q(ghi_chu__icontains=q) | Q(nguoi_kiem__icontains=q) | Q(kho__ten_kho__icontains=q) | Q(kho__ma_kho__icontains=q))
    if kho_filter:
        items = items.filter(kho_id=kho_filter)
    items = items[:20]
    return render(request, 'kho/kiem_ke_list.html', {
        'items': items,
        'q': q,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_filter,
        'page_title': 'Phiếu kiểm kê',
        'active_menu': 'kiem_ke'
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
    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'save' and kk.trang_thai == '1':
            ct_ids = request.POST.getlist('ct_id[]')
            sl_thuc_tes = request.POST.getlist('sl_thuc_te[]')
            for i, ct_id in enumerate(ct_ids):
                ct = KiemKe_CT.objects.get(pk=ct_id)
                ct.so_luong_thuc_te = int(sl_thuc_tes[i])
                ct.save()
            messages.success(request, 'Đã lưu số liệu kiểm kê (bước 1)')
            return redirect('kiem_ke_detail', pk=pk)

        if action == 'xac_nhan' and kk.trang_thai == '1':
            for ct in kk.chi_tiet.select_related('hang_hoa'):
                ton, _ = TonKho.objects.get_or_create(
                    hang_hoa=ct.hang_hoa,
                    kho=kk.kho,
                    defaults={'so_luong': 0, 'gia_von_tb': 0},
                )
                ton.so_luong = ct.so_luong_thuc_te
                ton.save(update_fields=['so_luong', 'ngay_cap_nhat'])

            kk.trang_thai = '2'
            kk.save(update_fields=['trang_thai'])
            messages.success(request, 'Đã xác nhận kiểm kê và cập nhật tồn kho (bước 2)')
            return redirect('kiem_ke_detail', pk=pk)

        if action == 'so_cai' and kk.trang_thai == '2':
            kk.trang_thai = '3'
            kk.save(update_fields=['trang_thai'])
            messages.success(request, 'Đã chuyển phiếu kiểm kê sang Sổ cái (bước 3)')
            return redirect('kiem_ke_detail', pk=pk)

        messages.error(request, 'Thao tác không hợp lệ theo trạng thái hiện tại')
        return redirect('kiem_ke_detail', pk=pk)
    return render(request, 'kho/kiem_ke_detail.html', {
        'kk': kk, 'chi_tiet': chi_tiet,
        'page_title': f'Kiểm kê {kk.kho.ten_kho}',
        'active_menu': 'kiem_ke',
    })


# ─── BÁO CÁO KHO ────────────────────────────────────────────
@login_required
def bao_cao_ton_kho(request):
    kho_id = request.GET.get('kho', '').strip()
    q = request.GET.get('q', '').strip()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()

    nhap_qs = PhieuNhap_CT.objects.select_related('phieu_nhap', 'hang_hoa', 'phieu_nhap__kho').filter(
        phieu_nhap__trang_thai__in=('2', '3')
    )
    xuat_qs = PhieuXuat_CT.objects.select_related('phieu_xuat', 'hang_hoa', 'phieu_xuat__kho').filter(
        phieu_xuat__trang_thai__in=('2', '3')
    )

    if kho_id:
        nhap_qs = nhap_qs.filter(phieu_nhap__kho_id=kho_id)
        xuat_qs = xuat_qs.filter(phieu_xuat__kho_id=kho_id)
    if q:
        nhap_qs = nhap_qs.filter(Q(hang_hoa__ma_hang__icontains=q) | Q(hang_hoa__ten_hang__icontains=q))
        xuat_qs = xuat_qs.filter(Q(hang_hoa__ma_hang__icontains=q) | Q(hang_hoa__ten_hang__icontains=q))

    if tu_ngay:
        dau_ky_nhap = nhap_qs.filter(phieu_nhap__ngay_chung_tu__lt=tu_ngay)
        dau_ky_xuat = xuat_qs.filter(phieu_xuat__ngay_chung_tu__lt=tu_ngay)
    else:
        dau_ky_nhap = nhap_qs.none()
        dau_ky_xuat = xuat_qs.none()

    sl_dau_ky_nhap = sum((i.so_luong_nhan or 0) for i in dau_ky_nhap)
    sl_dau_ky_xuat = sum((i.so_luong or 0) for i in dau_ky_xuat)
    gt_dau_ky_nhap = sum(int(i.thanh_tien or 0) for i in dau_ky_nhap)
    gt_dau_ky_xuat = sum(int(i.tong_gia_von or 0) for i in dau_ky_xuat)

    sl_dau_ky = sl_dau_ky_nhap - sl_dau_ky_xuat
    gt_dau_ky = gt_dau_ky_nhap - gt_dau_ky_xuat

    trong_ky_nhap = nhap_qs
    trong_ky_xuat = xuat_qs
    if tu_ngay and den_ngay:
        trong_ky_nhap = trong_ky_nhap.filter(phieu_nhap__ngay_chung_tu__range=[tu_ngay, den_ngay])
        trong_ky_xuat = trong_ky_xuat.filter(phieu_xuat__ngay_chung_tu__range=[tu_ngay, den_ngay])
    elif tu_ngay:
        trong_ky_nhap = trong_ky_nhap.filter(phieu_nhap__ngay_chung_tu__gte=tu_ngay)
        trong_ky_xuat = trong_ky_xuat.filter(phieu_xuat__ngay_chung_tu__gte=tu_ngay)
    elif den_ngay:
        trong_ky_nhap = trong_ky_nhap.filter(phieu_nhap__ngay_chung_tu__lte=den_ngay)
        trong_ky_xuat = trong_ky_xuat.filter(phieu_xuat__ngay_chung_tu__lte=den_ngay)

    trong_ky_nhap = trong_ky_nhap.order_by('phieu_nhap__ngay_chung_tu', 'phieu_nhap__so_phieu', 'id')
    trong_ky_xuat = trong_ky_xuat.order_by('phieu_xuat__ngay_chung_tu', 'phieu_xuat__so_phieu', 'id')

    sl_nhap_ky = sum((i.so_luong_nhan or 0) for i in trong_ky_nhap)
    gt_nhap_ky = sum(int(i.thanh_tien or 0) for i in trong_ky_nhap)
    sl_xuat_ky = sum((i.so_luong or 0) for i in trong_ky_xuat)
    gt_xuat_ky = sum(int(i.tong_gia_von or 0) for i in trong_ky_xuat)

    sl_cuoi_ky = sl_dau_ky + sl_nhap_ky - sl_xuat_ky
    gt_cuoi_ky = gt_dau_ky + gt_nhap_ky - gt_xuat_ky

    rows = []
    for i in trong_ky_nhap:
        rows.append({
            'sort_key': (i.phieu_nhap.ngay_chung_tu, i.phieu_nhap.so_phieu, 0, i.id),
            'loai_dong': 'nhap',
            'doi_tuong_id': i.phieu_nhap_id,
            'action_url': f'/kho/nhap/{i.phieu_nhap_id}/',
            'ngay_ghi_so': i.phieu_nhap.ngay_chung_tu,
            'ngay_ct': i.phieu_nhap.ngay_chung_tu,
            'ma_ct': 'PN',
            'so_ct': i.phieu_nhap.so_phieu,
            'dien_giai': i.phieu_nhap.ghi_chu or '',
            'ma_nhap_xuat': i.tk_no or '',
            'tk_doi_ung': i.tk_co or '',
            'gia': int(i.don_gia or 0),
            'sl_nhap': i.so_luong_nhan or 0,
            'tien_nhap': int(i.thanh_tien or 0),
            'sl_xuat': 0,
            'tien_xuat': 0,
        })
    for i in trong_ky_xuat:
        rows.append({
            'sort_key': (i.phieu_xuat.ngay_chung_tu, i.phieu_xuat.so_phieu, 1, i.id),
            'loai_dong': 'xuat',
            'doi_tuong_id': i.phieu_xuat_id,
            'action_url': f'/kho/xuat/{i.phieu_xuat_id}/',
            'ngay_ghi_so': i.phieu_xuat.ngay_chung_tu,
            'ngay_ct': i.phieu_xuat.ngay_chung_tu,
            'ma_ct': 'HD',
            'so_ct': i.phieu_xuat.so_phieu,
            'dien_giai': i.phieu_xuat.ghi_chu or '',
            'ma_nhap_xuat': '',
            'tk_doi_ung': '',
            'gia': int(i.gia_von or 0),
            'sl_nhap': 0,
            'tien_nhap': 0,
            'sl_xuat': i.so_luong or 0,
            'tien_xuat': int(i.tong_gia_von or 0),
        })

    rows.sort(key=lambda x: x['sort_key'])

    sl_ton_chay = sl_dau_ky
    gt_ton_chay = gt_dau_ky
    for r in rows:
        sl_ton_chay = sl_ton_chay + r['sl_nhap'] - r['sl_xuat']
        gt_ton_chay = gt_ton_chay + r['tien_nhap'] - r['tien_xuat']
        r['sl_ton'] = sl_ton_chay
        r['gt_ton'] = gt_ton_chay

    kho_da_chon = ''
    if kho_id:
        kho_obj = Kho.objects.filter(pk=kho_id).first()
        if kho_obj:
            kho_da_chon = f'{kho_obj.ma_kho} - {kho_obj.ten_kho}'

    return render(request, 'kho/bao_cao_ton.html', {
        'rows': rows,
        'kho_list': Kho.objects.filter(trang_thai=True),
        'kho_filter': kho_id,
        'kho_da_chon': kho_da_chon,
        'q': q,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'sl_dau_ky': int(sl_dau_ky),
        'gt_dau_ky': int(gt_dau_ky),
        'sl_nhap_ky': int(sl_nhap_ky),
        'gt_nhap_ky': int(gt_nhap_ky),
        'sl_xuat_ky': int(sl_xuat_ky),
        'gt_xuat_ky': int(gt_xuat_ky),
        'sl_cuoi_ky': int(sl_cuoi_ky),
        'gt_cuoi_ky': int(gt_cuoi_ky),
        'page_title': 'Sổ kho/Chi tiết vật tư',
        'active_menu': 'bao_cao_kho',
    })
