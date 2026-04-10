from django.urls import path

from . import views

urlpatterns = [
    path('', views.don_ban_list, name='don_ban_list'),
    path('them/', views.don_ban_them, name='don_ban_them'),
    path('api/khach-hang/', views.khach_hang_lookup, name='khach_hang_lookup'),
    path('api/khach-hang-lookup/', views.khach_hang_api_lookup, name='khach_hang_api_lookup'),
    path('api/don-ban-lookup/', views.don_ban_api_lookup, name='don_ban_api_lookup'),
    path('api/don-ban/<int:pk>/', views.don_ban_api_detail, name='don_ban_api_detail'),
    path('<int:pk>/', views.don_ban_detail, name='don_ban_detail'),
    path('<int:pk>/sua/', views.don_ban_sua, name='don_ban_sua'),
    path('<int:pk>/xoa/', views.don_ban_xoa, name='don_ban_xoa'),
    path('<int:pk>/so-cai/', views.don_ban_chuyen_so_cai, name='don_ban_chuyen_so_cai'),

    path('hoa-don/', views.hoa_don_ban_list, name='hoa_don_ban_list'),
    path('hoa-don/them/', views.hoa_don_ban_them, name='hoa_don_ban_them'),
    path('hoa-don/export-data/', views.hoa_don_ban_export_data, name='hoa_don_ban_export_data'),
    path('hoa-don/export-template/', views.hoa_don_ban_export_template, name='hoa_don_ban_export_template'),
    path('hoa-don/import-excel/', views.hoa_don_ban_import_excel, name='hoa_don_ban_import_excel'),
    path('hoa-don/<int:pk>/', views.hoa_don_ban_detail, name='hoa_don_ban_detail'),
    path('hoa-don/<int:pk>/copy/', views.hoa_don_ban_copy, name='hoa_don_ban_copy'),
    path('hoa-don/<int:pk>/sua/', views.hoa_don_ban_sua, name='hoa_don_ban_sua'),
    path('hoa-don/<int:pk>/xoa/', views.hoa_don_ban_xoa, name='hoa_don_ban_xoa'),
    path('hoa-don/<int:pk>/so-cai/', views.hoa_don_ban_chuyen_so_cai, name='hoa_don_ban_chuyen_so_cai'),
    path('hoa-don/<int:pk>/in/', views.hoa_don_ban_in, name='hoa_don_ban_in'),

    path('gia-ban/', views.gia_ban_list, name='gia_ban_list'),
    path('gia-ban/them/', views.gia_ban_them, name='gia_ban_them'),
    path('gia-ban/export-template/', views.gia_ban_export_template, name='gia_ban_export_template'),
    path('gia-ban/import-excel/', views.gia_ban_import_excel, name='gia_ban_import_excel'),
    path('gia-ban/<int:pk>/copy/', views.gia_ban_copy, name='gia_ban_copy'),
    path('gia-ban/<int:pk>/sua/', views.gia_ban_sua, name='gia_ban_sua'),
    path('gia-ban/<int:pk>/xoa/', views.gia_ban_xoa, name='gia_ban_xoa'),
    path('gia-ban/api/hang-hoa/', views.gia_ban_hang_hoa_api, name='gia_ban_hang_hoa_api'),

    path('phieu-thu/', views.phieu_thu_list, name='phieu_thu_list'),
    path('phieu-thu/them/', views.phieu_thu_them, name='phieu_thu_them'),
    path('phieu-thu/<int:pk>/xac-nhan/', views.phieu_thu_xac_nhan, name='phieu_thu_xac_nhan'),
    path('phieu-thu/<int:pk>/so-cai/', views.phieu_thu_chuyen_so_cai, name='phieu_thu_chuyen_so_cai'),
    path('cong-no/', views.cong_no_kh, name='cong_no_kh'),
    path('bao-cao/doanh-thu/', views.bao_cao_doanh_thu, name='bao_cao_doanh_thu'),
]
