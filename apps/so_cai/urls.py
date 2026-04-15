from django.urls import path

from . import views

urlpatterns = [
    path('', views.so_cai_view, name='so_cai'),
    path('ky-ke-toan/', views.ky_ke_toan_view, name='ky_ke_toan'),
    path('post/', views.post_document_view, name='so_cai_post_document'),
    path('api/post-to-ledger/', views.post_to_ledger_api, name='so_cai_api_post_to_ledger'),
    path('api/general-ledger/', views.general_ledger_api, name='so_cai_api_general_ledger'),
    path('api/trial-balance/', views.trial_balance_api, name='so_cai_api_trial_balance'),
]
