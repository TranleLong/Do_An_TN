from django.urls import path

from . import views

urlpatterns = [
    path('don-mua/', views.don_mua_list, name='don_mua_list'),
    path('don-mua/them/', views.don_mua_them, name='don_mua_them'),
    path('don-mua/<int:pk>/', views.don_mua_detail, name='don_mua_detail'),
    path('don-mua/<int:pk>/duyet/', views.don_mua_duyet, name='don_mua_duyet'),
    path('hoa-don-mua/', views.hoa_don_mua_list, name='hoa_don_mua_list'),
    path('hoa-don-mua/them/', views.hoa_don_mua_them, name='hoa_don_mua_them'),
    path('phieu-chi/', views.phieu_chi_list, name='phieu_chi_list'),
    path('phieu-chi/them/', views.phieu_chi_them, name='phieu_chi_them'),
    path('phieu-chi/<int:pk>/sua/', views.phieu_chi_sua, name='phieu_chi_sua'),
    path('phieu-chi/<int:pk>/xoa/', views.phieu_chi_xoa, name='phieu_chi_xoa'),
    path('phieu-chi/xoa-nhieu/', views.phieu_chi_xoa_nhieu, name='phieu_chi_xoa_nhieu'),
    path('phieu-chi/<int:pk>/xac-nhan/', views.phieu_chi_xac_nhan, name='phieu_chi_xac_nhan'),
    path('phieu-chi/<int:pk>/so-cai/', views.phieu_chi_chuyen_so_cai, name='phieu_chi_chuyen_so_cai'),
    path('cong-no-ncc/', views.cong_no_ncc, name='cong_no_ncc'),
]
