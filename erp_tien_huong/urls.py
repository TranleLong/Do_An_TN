"""ERP Tiến Hương - Main URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dang-nhap/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('dang-xuat/', auth_views.LogoutView.as_view(), name='logout'),
    path('', core_views.dashboard, name='dashboard'),
    path('hang-hoa/', include('apps.core.urls')),
    path('kho/', include('apps.kho.urls')),
    path('ban-hang/', include('apps.ban_hang.urls')),
    path('mua-hang/', include('apps.mua_hang.urls')),
    path('danh-muc/', include('apps.danh_muc.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
