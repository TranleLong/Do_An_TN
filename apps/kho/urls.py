from django.urls import path
from . import views

urlpatterns = [
    # ─── Tồn kho & Sơ đồ kho
    path('ton-kho/', views.ton_kho_list, name='ton_kho_list'),
    path('so-do-kho/', views.so_do_kho, name='so_do_kho'),

    # ─── Phiếu xuất kho (Thủ kho thao tác)
    path('xuat/', views.phieu_xuat_list, name='phieu_xuat_list'),
    path('xuat/them/', views.phieu_xuat_them, name='phieu_xuat_them'),

    # ─── Phiếu nhập (giữ lại nếu cần điều chỉnh tồn)
    path('nhap/', views.phieu_nhap_list, name='phieu_nhap_list'),
    path('nhap/them/', views.phieu_nhap_them, name='phieu_nhap_them'),
    path('nhap/<int:pk>/', views.phieu_nhap_detail, name='phieu_nhap_detail'),
    path('nhap/<int:pk>/xac-nhan/', views.phieu_nhap_xac_nhan, name='phieu_nhap_xac_nhan'),

    # ─── Kiểm kê kho
    path('kiem-ke/', views.kiem_ke_list, name='kiem_ke_list'),
    path('kiem-ke/them/', views.kiem_ke_them, name='kiem_ke_them'),
    path('kiem-ke/<int:pk>/', views.kiem_ke_detail, name='kiem_ke_detail'),

    # ─── Kế toán kho
    path('ke-toan/tinh-gia-xuat/', views.tinh_gia_xuat, name='tinh_gia_xuat'),
    path('ke-toan/doi-chieu/', views.doi_chieu_so_lieu, name='doi_chieu_so_lieu'),

    # ─── Báo cáo
    path('bao-cao/ton-kho/', views.bao_cao_ton_kho, name='bao_cao_ton_kho'),
]

