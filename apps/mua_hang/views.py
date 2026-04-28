# from datetime import date
# from decimal import Decimal, InvalidOperation

# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import get_object_or_404, redirect, render

# from apps.mua_hang.models import PhieuChi
# from apps.so_cai.periods import guard_accounting_period_error


# @login_required
# def cong_no_ncc(request):
#     """View gộp công nợ NCC"""
#     from apps.danh_muc.models import KhachHang, NhaCungCap

#     ds_ncc = NhaCungCap.objects.all()
#     return render(
#         request,
#         'ban_hang/cong_no_tong_hop.html',
#         {
#             'khach_hang_no': KhachHang.objects.all(),
#             'ncc_no': ds_ncc,
#             'page_title': 'Sổ chi tiết công nợ',
#             'active_menu': 'cong_no_ncc',
#         },
#     )


# @login_required
# def don_mua_list(request):
#     return render(
#         request,
#         'mua_hang/don_mua_list.html',
#         {'page_title': 'Quản lý Mua hàng', 'active_menu': 'don_mua'},
#     )


# @login_required
# def don_mua_them(request):
#     return redirect('don_mua_list')


# @login_required
# def don_mua_detail(request, pk):
#     return redirect('don_mua_list')


# @login_required
# def don_mua_duyet(request, pk):
#     return redirect('don_mua_list')


# @login_required
# def hoa_don_mua_list(request):
#     return redirect('don_mua_list')


# @login_required
# def hoa_don_mua_them(request):
#     return redirect('don_mua_list')


# @login_required
# def phieu_chi_list(request):
#     items = PhieuChi.objects.select_related('nha_cung_cap').order_by('-ngay_chi')[:50]
#     return render(
#         request,
#         'ban_hang/phieu_thu_list.html',
#         {
#             'items': items,
#             'page_title': 'Phiếu chi tiền',
#             'active_menu': 'phieu_chi',
#             'loai': 'chi',
#         },
#     )


# @login_required
# def phieu_chi_them(request):
#     from apps.danh_muc.models import NhaCungCap

#     copy_from = request.GET.get('copy_from')
#     phieu_copy = None
#     if copy_from:
#         phieu_copy = PhieuChi.objects.filter(pk=copy_from).first()
#         if phieu_copy:
#             phieu_copy.so_phieu = ''

#     if request.method == 'POST':
#         data = request.POST
#         try:
#             tong_chi = Decimal(data.get('so_tien', '0') or '0')
#         except InvalidOperation:
#             messages.error(request, 'Số tiền chi không hợp lệ')
#             return redirect('phieu_chi_them')

#         if tong_chi <= 0:
#             messages.error(request, 'Số tiền chi phải lớn hơn 0')
#             return redirect('phieu_chi_them')

#         ncc_id = data.get('doi_tuong') or None
#         if not ncc_id:
#             messages.error(request, 'Vui lòng chọn nhà cung cấp cho phiếu chi')
#             return redirect('phieu_chi_them')

#         so_phieu = data.get('so_phieu') or f"PC-{date.today().strftime('%Y%m%d')}"
#         phieu = PhieuChi.objects.create(
#             so_phieu=so_phieu,
#             ngay_chi=data.get('ngay') or date.today(),
#             nha_cung_cap_id=ncc_id,
#             hinh_thuc=data.get('hinh_thuc', 'tien_mat'),
#             tong_chi=tong_chi,
#             ghi_chu=data.get('ly_do', ''),
#             nguoi_tao=request.user,
#         )
#         messages.success(request, f'Đã lưu phiếu chi {phieu.so_phieu} thành công!')
#         return redirect('phieu_chi_list')

#     so_phieu_default = f"PC-{date.today().strftime('%Y%m%d')}"
#     return render(
#         request,
#         'ban_hang/phieu_thu_chi_form.html',
#         {
#             'loai': 'chi',
#             'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
#             'page_title': 'Lập Phiếu Chi',
#             'so_phieu_default': so_phieu_default,
#             'phieu': phieu_copy,
#             'today': date.today(),
#             'active_menu': 'phieu_chi',
#         },
#     )


# @login_required
# def phieu_chi_sua(request, pk):
#     from apps.danh_muc.models import NhaCungCap
    
#     phieu = get_object_or_404(PhieuChi, pk=pk)
#     if request.method == 'POST':
#         data = request.POST
#         try:
#             tong_chi = Decimal(data.get('so_tien', phieu.tong_chi or 0) or 0)
#         except InvalidOperation:
#             messages.error(request, 'Số tiền chi không hợp lệ')
#             return render(request, 'ban_hang/phieu_thu_chi_form.html', {
#                 'loai': 'chi',
#                 'phieu': phieu,
#                 'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
#                 'page_title': 'Cập nhật Phiếu Chi',
#                 'today': date.today(),
#                 'active_menu': 'phieu_chi',
#             })
        
#         if tong_chi <= 0:
#             messages.error(request, 'Số tiền chi phải lớn hơn 0')
#             return render(request, 'ban_hang/phieu_thu_chi_form.html', {
#                 'loai': 'chi',
#                 'phieu': phieu,
#                 'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
#                 'page_title': 'Cập nhật Phiếu Chi',
#                 'today': date.today(),
#                 'active_menu': 'phieu_chi',
#             })
        
#         ncc_id = data.get('doi_tuong') or phieu.nha_cung_cap_id
#         if not ncc_id:
#             messages.error(request, 'Vui lòng chọn nhà cung cấp cho phiếu chi')
#             return render(request, 'ban_hang/phieu_thu_chi_form.html', {
#                 'loai': 'chi',
#                 'phieu': phieu,
#                 'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
#                 'page_title': 'Cập nhật Phiếu Chi',
#                 'today': date.today(),
#                 'active_menu': 'phieu_chi',
#             })
        
#         phieu.ngay_chi = data.get('ngay') or phieu.ngay_chi or date.today()
#         phieu.nha_cung_cap_id = ncc_id
#         phieu.hinh_thuc = data.get('hinh_thuc', 'tien_mat')
#         phieu.tong_chi = tong_chi
#         phieu.ghi_chu = data.get('ly_do', '')
#         phieu.save()
        
#         messages.success(request, f'Đã cập nhật phiếu chi {phieu.so_phieu} thành công!')
#         return redirect('phieu_chi_list')
    
#     return render(request, 'ban_hang/phieu_thu_chi_form.html', {
#         'loai': 'chi',
#         'phieu': phieu,
#         'ncc_list': NhaCungCap.objects.filter(trang_thai=True),
#         'page_title': 'Cập nhật Phiếu Chi',
#         'today': date.today(),
#         'active_menu': 'phieu_chi',
#     })


# @login_required
# def phieu_chi_xoa(request, pk):
#     phieu = get_object_or_404(PhieuChi, pk=pk)
#     if request.method == 'POST':
#         so_phieu = phieu.so_phieu
#         phieu.delete()
#         messages.success(request, f'Đã xóa phiếu chi {so_phieu}')
#         return redirect('phieu_chi_list')
    
#     return render(request, 'ban_hang/phieu_thu_chi_form.html', {
#         'loai': 'chi',
#         'phieu': phieu,
#         'confirm_delete': True,
#     })


# @login_required
# def phieu_chi_xoa_nhieu(request):
#     if request.method == 'POST':
#         ids = request.POST.getlist('ids[]')
#         phieus = PhieuChi.objects.filter(pk__in=ids)
#         count = phieus.count()
#         phieus.delete()
#         messages.success(request, f'Đã xóa {count} phiếu chi')
#         return redirect('phieu_chi_list')
    
#     return redirect('phieu_chi_list')


# @login_required
# def phieu_chi_xac_nhan(request, pk):
#     phieu = get_object_or_404(PhieuChi, pk=pk)
#     if request.method == 'POST':
#         if phieu.trang_thai == '2':
#             messages.info(request, f'Phiếu chi {phieu.so_phieu} đã ở trạng thái Chuyển sổ cái')
#         elif phieu.trang_thai == '1':
#             phieu.trang_thai = '2'
#             phieu.save(update_fields=['trang_thai'])
#             messages.success(request, f'Đã chuyển phiếu chi {phieu.so_phieu} sang Sổ cái')
#         else:
#             messages.error(request, 'Chỉ phiếu chi ở bước 1 mới xác nhận được')
#     return redirect('phieu_chi_list')


# @login_required
# def phieu_chi_chuyen_so_cai(request, pk):
#     phieu = get_object_or_404(PhieuChi, pk=pk)
#     if request.method == 'POST':
#         if phieu.trang_thai == '2':
#             messages.info(request, f'Phiếu chi {phieu.so_phieu} đã ở trạng thái Chuyển sổ cái')
#         elif phieu.trang_thai == '1':
#             phieu.trang_thai = '2'
#             phieu.save(update_fields=['trang_thai'])
#             messages.success(request, f'Đã chuyển phiếu chi {phieu.so_phieu} sang Sổ cái')
#         else:
#             messages.error(request, 'Chỉ phiếu chi ở bước 1 mới chuyển được Sổ cái')
#     return redirect('phieu_chi_list')


# _period_guard_fallbacks = {
#     'phieu_chi_them': 'phieu_chi_list',
#     'phieu_chi_sua': 'phieu_chi_list',
#     'phieu_chi_xoa': 'phieu_chi_list',
#     'phieu_chi_xoa_nhieu': 'phieu_chi_list',
# }

# for _view_name, _fallback in _period_guard_fallbacks.items():
#     if _view_name in globals():
#         globals()[_view_name] = guard_accounting_period_error(_fallback)(globals()[_view_name])
