from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib.auth import logout
from .models import BusinessProfile

class BusinessLoginRequiredMixin(LoginRequiredMixin):
    """
    事業者としてのログインを必須とするMixin
    1. ログインしていない -> ビジネスログイン画面へ
    2. ログインしているが BusinessProfile がない -> ログアウトさせてビジネスログイン画面へ
    """
    login_url = 'biz_landing' 

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has BusinessProfile
        if not BusinessProfile.objects.filter(user=request.user).exists():
            # Worker or invalid user trying to access business page
            logout(request)
            return redirect('biz_landing')

        return super().dispatch(request, *args, **kwargs)
