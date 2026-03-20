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
    path('cong-no-ncc/', views.cong_no_ncc, name='cong_no_ncc'),
]
