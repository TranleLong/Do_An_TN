from django.urls import path
from . import views

urlpatterns = [
    path('khach-hang/', views.kh_list, name='kh_list'),
    path('khach-hang/them/', views.kh_form, name='kh_them'),
    path('khach-hang/<int:pk>/sua/', views.kh_form, name='kh_sua'),
    path('khach-hang/<int:pk>/xoa/', views.kh_xoa, name='kh_xoa'),
    path('nha-cung-cap/', views.ncc_list, name='ncc_list'),
    path('nha-cung-cap/them/', views.ncc_form, name='ncc_them'),
    path('nha-cung-cap/<int:pk>/sua/', views.ncc_form, name='ncc_sua'),
    path('nha-cung-cap/<int:pk>/xoa/', views.ncc_xoa, name='ncc_xoa'),
]
