from django.urls import path
from . import views

urlpatterns = [
    path('', views.don_ban_list, name='don_ban_list'),
    path('them/', views.don_ban_them, name='don_ban_them'),
    path('<int:pk>/', views.don_ban_detail, name='don_ban_detail'),
    path('<int:pk>/xac-nhan/', views.don_ban_xac_nhan, name='don_ban_xac_nhan'),
    path('<int:pk>/huy/', views.don_ban_huy, name='don_ban_huy'),
    path('phieu-thu/', views.phieu_thu_list, name='phieu_thu_list'),
    path('phieu-thu/them/', views.phieu_thu_them, name='phieu_thu_them'),
    path('cong-no/', views.cong_no_kh, name='cong_no_kh'),
    path('bao-cao/doanh-thu/', views.bao_cao_doanh_thu, name='bao_cao_doanh_thu'),
]
