import os

file_path = 'apps/ban_hang/views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("don_id = (data.get('don_ban') or None) if loai_phieu == '1' else None", "hoa_don_id = (data.get('hoa_don') or None) if loai_phieu == '1' else None")
content = content.replace("don = DonBan.objects.filter(pk=don_id).first() if (don_id and loai_phieu == '1') else None", "hoa_don_obj = HoaDonBan.objects.filter(pk=hoa_don_id).first() if (hoa_don_id and loai_phieu == '1') else None")
content = content.replace("kh_id = data.get('khach_hang') or (don.khach_hang_id if don else None)", "kh_id = data.get('khach_hang') or (hoa_don_obj.khach_hang_id if hoa_don_obj else None)")
content = content.replace("_build_phieu_thu_context(form_values, don, mode=mode)", "_build_phieu_thu_context(form_values, hoa_don_obj, mode=mode)")
content = content.replace("if not don:", "if not hoa_don_obj:")

content = content.replace("""
            cash_invoice = _get_don_cash_invoice(don)
            if cash_invoice:
                messages.error(request, f'Chứng từ bán hàng đã hạch toán thu tiền ngay (Nợ {cash_invoice.tk_no} - Hóa đơn {cash_invoice.so_hoa_don}), không được tạo thêm phiếu thu tránh ghi trùng.')
                return render(request, 'ban_hang/phieu_thu_form.html', _build_phieu_thu_context(form_values, don, mode=mode))

            if not _is_don_ghi_nhan_cong_no(don):
                messages.error(request, 'Đơn hàng chưa có hóa đơn hạch toán công nợ TK 131 nên không thể thu nợ.')
                return render(request, 'ban_hang/phieu_thu_form.html', _build_phieu_thu_context(form_values, don, mode=mode))
            if tong_thu > Decimal(don.con_no or 0):
                messages.error(request, f'Số tiền thu vượt công nợ còn lại ({Decimal(don.con_no or 0):,.0f} đ)')
                return render(request, 'ban_hang/phieu_thu_form.html', _build_phieu_thu_context(form_values, don, mode=mode))
""",
"""
            if str(hoa_don_obj.tk_no or '') not in ('131', '111', '112'):
                messages.error(request, 'Hóa đơn không được hạch toán vào TK có thể thu tiền.')
                return render(request, 'ban_hang/phieu_thu_form.html', _build_phieu_thu_context(form_values, hoa_don_obj, mode=mode))
            
            # Đối với hóa đơn công nợ, không thu quá số dư nợ
            if str(hoa_don_obj.tk_no or '') == '131':
                if tong_thu > Decimal(hoa_don_obj.con_no or 0):
                    messages.error(request, f'Số tiền thu vượt công nợ còn lại ({Decimal(hoa_don_obj.con_no or 0):,.0f} đ)')
                    return render(request, 'ban_hang/phieu_thu_form.html', _build_phieu_thu_context(form_values, hoa_don_obj, mode=mode))
""")

content = content.replace("don.tinh_tong()", "hoa_don_obj.tinh_tong() if hoa_don_obj else None")
content = content.replace("phieu.don_ban", "phieu.hoa_don")
content = content.replace("phieu.don_ban_id", "phieu.hoa_don_id")
content = content.replace("don = phieu.don_ban", "hoa_don_obj = phieu.hoa_don")
content = content.replace("if phieu.don_ban:", "if phieu.hoa_don:")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
