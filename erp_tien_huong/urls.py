"""ERP Tiến Hương - Main URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.danh_muc import views as danh_muc_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dang-nhap/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('dang-xuat/', auth_views.LogoutView.as_view(), name='logout'),
    path('', danh_muc_views.dashboard, name='dashboard'),
    path('kho/', include('apps.kho.urls')),
    path('ban-hang/', include('apps.ban_hang.urls')),
    path('mua-hang/', include('apps.mua_hang.urls')),
    path('so-cai/', include('apps.so_cai.urls')),
    path('danh-muc/', include('apps.danh_muc.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
