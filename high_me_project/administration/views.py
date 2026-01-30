from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin

# 1. Admin Login View
class AdminLoginView(LoginView):
    template_name = 'administration/login.html'
    
    def get_success_url(self):
        return '/administration/dashboard/'

# 2. Main Dashboard
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'administration/dashboard.html'

# 3. Application Screening (Reference: 応募審査画面)
class ApplicationScreeningView(LoginRequiredMixin, TemplateView):
    template_name = 'administration/application_screening.html'

# 4. Company List (Reference: 企業一覧画面)
class CompanyListView(LoginRequiredMixin, TemplateView):
    template_name = 'administration/company_list.html'
