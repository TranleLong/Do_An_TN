from django.urls import path

from . import views

urlpatterns = [
    # ─── Tồn kho & Sơ đồ kho
    path('ton-kho/', views.ton_kho_list, name='ton_kho_list'),
    path('ton-kho/thiet-lap-muc-ton/', views.thiet_lap_muc_ton_kho, name='thiet_lap_muc_ton_kho'),
    path('so-do-kho/', views.so_do_kho, name='so_do_kho'),
    path('so-do-kho/gan-vi-tri/ajax/', views.gan_vi_tri_thu_cong, name='gan_vi_tri_thu_cong'),
    path('so-do-kho/chuyen-vi-tri/ajax/', views.chuyen_vi_tri_thu_cong, name='chuyen_vi_tri_thu_cong'),
    path('vi-tri/<int:pk>/chi-tiet/', views.chi_tiet_vi_tri, name='chi_tiet_vi_tri'),

    # ─── Phiếu xuất kho (Thủ kho thao tác)
    path('xuat/', views.phieu_xuat_list, name='phieu_xuat_list'),
    path('xuat/them/', views.phieu_xuat_them, name='phieu_xuat_them'),
    path('xuat/export-data/', views.phieu_xuat_export_data, name='phieu_xuat_export_data'),
    path('xuat/export-template/', views.phieu_xuat_export_template, name='phieu_xuat_export_template'),
    path('xuat/import-excel/', views.phieu_xuat_import_excel, name='phieu_xuat_import_excel'),
    path('xuat/xoa-nhieu/', views.phieu_xuat_xoa_nhieu, name='phieu_xuat_xoa_nhieu'),
    path('xuat/<int:pk>/sua/', views.phieu_xuat_sua, name='phieu_xuat_sua'),
    path('xuat/<int:pk>/xoa/', views.phieu_xuat_xoa, name='phieu_xuat_xoa'),
    path('xuat/<int:pk>/', views.phieu_xuat_detail, name='phieu_xuat_detail'),
    path('xuat/<int:pk>/xac-nhan/', views.phieu_xuat_xac_nhan, name='phieu_xuat_xac_nhan'),
    path('xuat/<int:pk>/so-cai/', views.phieu_xuat_chuyen_so_cai, name='phieu_xuat_chuyen_so_cai'),

    # ─── Phiếu nhập (giữ lại nếu cần điều chỉnh tồn)
    path('nhap/', views.phieu_nhap_list, name='phieu_nhap_list'),
    path('nhap/them/', views.phieu_nhap_them, name='phieu_nhap_them'),
    path('nhap/export-data/', views.phieu_nhap_export_data, name='phieu_nhap_export_data'),
    path('nhap/export-template/', views.phieu_nhap_export_template, name='phieu_nhap_export_template'),
    path('nhap/import-excel/', views.phieu_nhap_import_excel, name='phieu_nhap_import_excel'),
    path('nhap/xoa-nhieu/', views.phieu_nhap_xoa_nhieu, name='phieu_nhap_xoa_nhieu'),
    path('nhap/<int:pk>/sua/', views.phieu_nhap_sua, name='phieu_nhap_sua'),
    path('nhap/<int:pk>/xoa/', views.phieu_nhap_xoa, name='phieu_nhap_xoa'),
    path('nhap/<int:pk>/in/', views.phieu_nhap_in, name='phieu_nhap_in'),
    path('nhap/goi-y-vi-tri/', views.goi_y_vi_tri_nhap, name='goi_y_vi_tri_nhap'),
    path('nhap/<int:pk>/', views.phieu_nhap_detail, name='phieu_nhap_detail'),
    path('nhap/<int:pk>/xac-nhan/', views.phieu_nhap_xac_nhan, name='phieu_nhap_xac_nhan'),
    path('nhap/<int:pk>/so-cai/', views.phieu_nhap_chuyen_so_cai, name='phieu_nhap_chuyen_so_cai'),

    # ─── Kiểm kê kho
    path('kiem-ke/', views.kiem_ke_list, name='kiem_ke_list'),
    path('kiem-ke/export-data/', views.kiem_ke_export_data, name='kiem_ke_export_data'),
    path('kiem-ke/them/', views.kiem_ke_them, name='kiem_ke_them'),
    path('kiem-ke/<int:pk>/', views.kiem_ke_detail, name='kiem_ke_detail'),
    path('kiem-ke/<int:pk>/xoa/', views.kiem_ke_xoa, name='kiem_ke_xoa'),
    path('kiem-ke/xoa-nhieu/', views.kiem_ke_xoa_nhieu, name='kiem_ke_xoa_nhieu'),
    path('kiem-ke/<int:pk>/in/', views.kiem_ke_in, name='kiem_ke_in'),
    path('kiem-ke/dieu-chinh/', views.kiem_ke_dieu_chinh_list, name='kiem_ke_dieu_chinh_list'),
    path('kiem-ke/dieu-chinh/<int:pk>/', views.kiem_ke_dieu_chinh_detail, name='kiem_ke_dieu_chinh_detail'),
    path('kiem-ke/dieu-chinh/<int:pk>/xoa/', views.kiem_ke_dieu_chinh_xoa, name='kiem_ke_dieu_chinh_xoa'),

    # ─── Kế toán kho
    path('ke-toan/tinh-gia-xuat/', views.tinh_gia_xuat, name='tinh_gia_xuat'),
    path('ke-toan/doi-chieu/', views.doi_chieu_so_lieu, name='doi_chieu_so_lieu'),

    # ─── Báo cáo
    path('bao-cao/xuat-nhap-ton/', views.bao_cao_xuat_nhap_ton, name='bao_cao_xuat_nhap_ton'),
    path('bao-cao/so-chi-tiet-hang-hoa/', views.bao_cao_ton_kho, name='so_chi_tiet_hang_hoa'),
    path('bao-cao/ton-kho-hien-tai/', views.bao_cao_ton_hien_tai, name='bao_cao_ton_hien_tai'),
    path('bao-cao/ton-kho/', views.bao_cao_ton_kho, name='bao_cao_ton_kho'),
    path('bao-cao/ton-kho-loi/', views.bao_cao_ton_kho_loi, name='bao_cao_ton_kho_loi'),
]

