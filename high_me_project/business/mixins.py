from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib.auth import logout
from .models import BusinessProfile

class BusinessLoginRequiredMixin(LoginRequiredMixin):
    """
    事業者としてのログインを必須とするMixin
    1. ログインしていない -> ビジネスログイン画面へ
    2. ログインしているが BusinessProfile がない -> 事業者登録画面へ
    """
    login_url = 'biz_login' 

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has BusinessProfile
        # hasattr is risky if DoesNotExist is raised, so use exists()
        if not BusinessProfile.objects.filter(user=request.user).exists():
            if request.user.is_superuser:
                return super().dispatch(request, *args, **kwargs)
            # If no profile, they might need to complete registration
            return redirect('biz_business_register')

        return super().dispatch(request, *args, **kwargs)
