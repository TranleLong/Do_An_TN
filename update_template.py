import os

file_path = 'templates/ban_hang/phieu_thu_form.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace modal and search elements
content = content.replace('#modalDonBan', '#modalHoaDon')
content = content.replace('id="modalDonBan"', 'id="modalHoaDon"')
content = content.replace('Danh mục đơn bán', 'Danh mục hóa đơn bán')
content = content.replace('id="donSearchInput"', 'id="hoaDonSearchInput"')
content = content.replace('id="donSearchResults"', 'id="hoaDonSearchResults"')
content = content.replace('placeholder="Tìm nhanh số đơn hoặc mã khách..."', 'placeholder="Tìm nhanh số hóa đơn hoặc mã khách..."')

# Replace lookup and select elements
content = content.replace('list="don_lookup_list"', 'list="hoa_don_lookup_list"')
content = content.replace('id="don_display"', 'id="hoa_don_display"')
content = content.replace('placeholder="Chọn đơn bán liên kết"', 'placeholder="Chọn hóa đơn liên kết"')
content = content.replace('id="btnSearchDon"', 'id="btnSearchHoaDon"')
content = content.replace('Tra cứu đơn bán', 'Tra cứu hóa đơn')

content = content.replace('name="don_ban"', 'name="hoa_don"')
content = content.replace('id="don_ban"', 'id="hoa_don"')
content = content.replace('{% for don in don_ban_list %}', '{% for hd in hoa_don_list %}')
content = content.replace('don.pk', 'hd.pk')
content = content.replace('don.so_don', 'hd.so_hoa_don')
content = content.replace('don.ngay_chung_tu', 'hd.ngay_lap')
content = content.replace('don.con_no', 'hd.con_no')
content = content.replace('don.khach_hang.ma_kh', 'hd.khach_hang.ma_kh')
content = content.replace('don.ten_kh', 'hd.ten_kh')
content = content.replace('don.khach_hang_id', 'hd.khach_hang_id')
content = content.replace('form_values.don_ban', 'form_values.hoa_don')
content = content.replace('{{ don.so_don }} - {{ don.ten_kh }}', '{{ hd.so_hoa_don }} - {{ hd.ten_kh }}')

content = content.replace('id="don_lookup_list"', 'id="hoa_don_lookup_list"')

# Replace table headers and previews
content = content.replace('<th>Số hóa đơn / đơn</th>', '<th>Số hóa đơn</th>')
content = content.replace('id="previewSoDon"', 'id="previewSoHoaDon"')

# JS replacements
content = content.replace('let donModal = null;', 'let hoaDonModal = null;')
content = content.replace("syncLookupInputToSelect('#don_display', '#don_ban');", "syncLookupInputToSelect('#hoa_don_display', '#hoa_don');")
content = content.replace("$('#don_ban').on('change', updateDonPreviewFromSelect);", "$('#hoa_don').on('change', updateHoaDonPreviewFromSelect);")
content = content.replace('function updateDonPreviewFromSelect()', 'function updateHoaDonPreviewFromSelect()')
content = content.replace("$('#don_ban option:selected')", "$('#hoa_don option:selected')")
content = content.replace("$('#don_display').val('');", "$('#hoa_don_display').val('');")
content = content.replace('updateDonPreviewFromSelect();', 'updateHoaDonPreviewFromSelect();')

content = content.replace('function loadDonResults()', 'function loadHoaDonResults()')
content = content.replace("$('#donSearchInput').val().trim()", "$('#hoaDonSearchInput').val().trim()")
content = content.replace('{% url "don_ban_api_lookup" %}', '{% url "hoa_don_ban_api_lookup" %}')
content = content.replace("$('#donSearchResults').html", "$('#hoaDonSearchResults').html")
content = content.replace('btn-don-select', 'btn-hoa-don-select')
content = content.replace('donSearchInput', 'hoaDonSearchInput')
content = content.replace('loadDonResults', 'loadHoaDonResults')

content = content.replace("$('#btnSearchDon')", "$('#btnSearchHoaDon')")
content = content.replace('if (!donModal)', 'if (!hoaDonModal)')
content = content.replace('donModal = new bootstrap.Modal', 'hoaDonModal = new bootstrap.Modal')
content = content.replace('donModal.show()', 'hoaDonModal.show()')
content = content.replace("$(document).on('click', '.btn-don-select'", "$(document).on('click', '.btn-hoa-don-select'")
content = content.replace("$('#hoa_don').val(id)", "$('#hoa_don').val(id)")
content = content.replace('if (donModal)', 'if (hoaDonModal)')
content = content.replace('donModal.hide()', 'hoaDonModal.hide()')

content = content.replace('data-so-don', 'data-so-hoa-don')
content = content.replace("opt.data('so-don')", "opt.data('so-hoa-don')")
content = content.replace('soDon', 'soHoaDon')
content = content.replace("$('#previewSoHoaDon').text(soHoaDon)", "$('#previewSoHoaDon').text(soHoaDon)")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
