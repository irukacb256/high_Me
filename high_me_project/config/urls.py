"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts import views as account_views # accountsアプリのviewsをインポート
from jobs import views as job_views          # ★これを追加！

# config/urls.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.onboarding1, name='onboarding1'),
    path('step2/', account_views.onboarding2, name='onboarding2'),
    path('step3/', account_views.onboarding3, name='onboarding3'),
    path('gate/', account_views.gate, name='gate'),
    path('signup/', account_views.signup, name='signup'),
    
    # これを追加！ name='login' とすることでエラーが消えます
    path('login/', account_views.login_view, name='login'), 
    
    path('home/', job_views.index, name='index'),

    #ログイン画面 - 新規登録など
    path('signup/', account_views.signup, name='signup'),
    path('verify/dob/', account_views.verify_dob, name='verify_dob'), # 追加
    path('profile-setup/', account_views.profile_setup, name='profile_setup'),

]
