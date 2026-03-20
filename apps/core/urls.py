from django.urls import path
from . import views

urlpatterns = [
    path('', views.hang_hoa_list, name='hang_hoa_list'),
    path('them/', views.hang_hoa_form, name='hang_hoa_them'),
    path('<int:pk>/sua/', views.hang_hoa_form, name='hang_hoa_sua'),
    path('<int:pk>/xoa/', views.hang_hoa_xoa, name='hang_hoa_xoa'),
    path('api/tra-cuu/', views.hang_hoa_api, name='hang_hoa_api'),
    path('kho/', views.kho_list, name='kho_list'),
    path('nhom/', views.nhom_hang_list, name='nhom_hang_list'),
]
