from django.urls import path

from . import views

urlpatterns = [
    path('hang-hoa/', views.hang_hoa_list, name='hang_hoa_list'),
    path('hang-hoa/them/', views.hang_hoa_form, name='hang_hoa_them'),
    path('hang-hoa/<int:pk>/sua/', views.hang_hoa_form, name='hang_hoa_sua'),
    path('hang-hoa/<int:pk>/xoa/', views.hang_hoa_xoa, name='hang_hoa_xoa'),
    path('hang-hoa/xoa-nhieu/', views.hang_hoa_xoa_nhieu, name='hang_hoa_xoa_nhieu'),
    path('hang-hoa/api/tra-cuu/', views.hang_hoa_api, name='hang_hoa_api'),
    path('hang-hoa/api/lookup/', views.hang_hoa_lookup_api, name='hang_hoa_lookup_api'),
    path('kho/', views.kho_list, name='kho_list'),
    path('nhom-hang/', views.nhom_hang_list, name='nhom_hang_list'),
    path('don-vi-tinh/', views.don_vi_tinh_list, name='don_vi_tinh_list'),
    path('tai-khoan-ke-toan/', views.tai_khoan_ke_toan_list, name='tai_khoan_ke_toan_list'),
    path('tai-khoan-ke-toan/api/lookup/', views.tai_khoan_api_lookup, name='tai_khoan_api_lookup'),
    path('nha-cung-cap-kh/api/lookup/', views.nha_cung_cap_kh_api_lookup, name='nha_cung_cap_kh_api_lookup'),
    path('vi-tri-kho/', views.vi_tri_kho_list, name='vi_tri_kho_list'),
    path('vi-tri-kho/api/lookup/', views.vi_tri_kho_api_lookup, name='vi_tri_kho_api_lookup'),

    path('khach-hang/', views.kh_list, name='kh_list'),
    path('khach-hang/them/', views.kh_form, name='kh_them'),
    path('khach-hang/<int:pk>/sua/', views.kh_form, name='kh_sua'),
    path('khach-hang/<int:pk>/xoa/', views.kh_xoa, name='kh_xoa'),
    path('khach-hang/api/lookup-masothue/', views.kh_lookup_masothue, name='kh_lookup_masothue'),
    path(
        'khach-hang/<int:pk>/lich-su-mua-hang/',
        views.kh_lich_su_mua_hang,
        name='kh_lich_su_mua_hang',
    ),
    path('nha-cung-cap/', views.ncc_list, name='ncc_list'),
    path('nha-cung-cap/them/', views.ncc_form, name='ncc_them'),
    path('nha-cung-cap/<int:pk>/sua/', views.ncc_form, name='ncc_sua'),
    path('nha-cung-cap/<int:pk>/xoa/', views.ncc_xoa, name='ncc_xoa'),
]
