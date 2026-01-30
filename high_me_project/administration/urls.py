from django.urls import path
from .views import AdminLoginView, AdminDashboardView, ApplicationScreeningView, CompanyListView

urlpatterns = [
    # Login
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    
    # Dashboard (Main)
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Application Screening (応募審査)
    path('screening/', ApplicationScreeningView.as_view(), name='admin_screening'),
    
    # Company List (企業一覧)
    path('companies/', CompanyListView.as_view(), name='admin_companies'),
]
