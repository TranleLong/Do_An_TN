import os

file_path = 'apps/ban_hang/views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Thay thế ds don_ban -> hoa_don trong cac ham
content = content.replace('def _phieu_thu_don_ban_queryset():\n    return (\n        DonBan.objects.select_related(\'khach_hang\')\n        .filter(hoa_don_lien_ket__tk_no=\'131\', hoa_don_lien_ket__trang_thai__in=(\'2\', \'3\'))\n        .exclude(con_no=0)\n        .distinct()\n        .order_by(\'-ngay_chung_tu\', \'-id\')\n    )', 'def _phieu_thu_hoa_don_queryset():\n    return (\n        HoaDonBan.objects.select_related(\'khach_hang\')\n        .exclude(con_no=0)\n        .distinct()\n        .order_by(\'-ngay_lap\', \'-id\')\n    )')

content = content.replace('def _phieu_thu_khach_hang_cong_no_map():\n    don_qs = DonBan.objects.select_related(\'khach_hang\').filter(\n        khach_hang__isnull=False,\n        khach_hang__trang_thai=True,\n        hoa_don_lien_ket__tk_no=\'131\',\n        hoa_don_lien_ket__trang_thai__in=(\'2\', \'3\'),\n    ).distinct()\n\n    data = {}\n    for don in don_qs:\n        kh_id = don.khach_hang_id\n        if not kh_id:\n            continue\n        if kh_id not in data:\n            data[kh_id] = {\n                \'tong_hoa_don\': Decimal(\'0\'),\n                \'tong_da_thu\': Decimal(\'0\'),\n                \'con_no\': Decimal(\'0\'),\n            }\n        data[kh_id][\'tong_hoa_don\'] += Decimal(don.tong_thanh_toan or 0)\n        data[kh_id][\'tong_da_thu\'] += Decimal(don.da_thu or 0)', 'def _phieu_thu_khach_hang_cong_no_map():\n    hd_qs = HoaDonBan.objects.select_related(\'khach_hang\').filter(\n        khach_hang__isnull=False,\n        khach_hang__trang_thai=True,\n    ).distinct()\n\n    data = {}\n    for hd in hd_qs:\n        kh_id = hd.khach_hang_id\n        if not kh_id:\n            continue\n        if kh_id not in data:\n            data[kh_id] = {\n                \'tong_hoa_don\': Decimal(\'0\'),\n                \'tong_da_thu\': Decimal(\'0\'),\n                \'con_no\': Decimal(\'0\'),\n            }\n        data[kh_id][\'tong_hoa_don\'] += Decimal(hd.tong_cong or 0)\n        data[kh_id][\'tong_da_thu\'] += Decimal(hd.da_thu or 0)')

content = content.replace('don_ban__isnull=True', 'hoa_don__isnull=True')
content = content.replace('phieu.don_ban_id', 'phieu.hoa_don_id')

content = content.replace('def _build_phieu_thu_context(form_values=None, don_selected=None, editing=False, mode=\'thu\'):', 'def _build_phieu_thu_context(form_values=None, hoa_don_selected=None, editing=False, mode=\'thu\'):')
content = content.replace('don_ban_list = _phieu_thu_don_ban_queryset()', 'hoa_don_list = _phieu_thu_hoa_don_queryset()')
content = content.replace('    if don_selected and don_selected.pk:\n        don_ban_list = (don_ban_list | DonBan.objects.select_related(\'khach_hang\').filter(pk=don_selected.pk)).distinct()', '    if hoa_don_selected and hoa_don_selected.pk:\n        hoa_don_list = (hoa_don_list | HoaDonBan.objects.select_related(\'khach_hang\').filter(pk=hoa_don_selected.pk)).distinct()')

content = content.replace('\'don_ban_list\': don_ban_list,', '\'hoa_don_list\': hoa_don_list,')
content = content.replace('\'don_selected\': don_selected,', '\'hoa_don_selected\': hoa_don_selected,')
content = content.replace('\'don_ban\': data.get(\'don_ban\', \'\') if loai_phieu == \'1\' else \'\',', '\'hoa_don\': data.get(\'hoa_don\', \'\') if loai_phieu == \'1\' else \'\',')

content = content.replace('don_ban_id = phieu.don_ban_id', 'hoa_don_id = phieu.hoa_don_id')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
