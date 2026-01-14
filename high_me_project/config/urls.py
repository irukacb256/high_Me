# config/urls.py

from django.contrib import admin
from django.urls import path
from accounts import views as account_views
from jobs import views as job_views
from business import views as biz_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- オンボーディング ---
    path('', account_views.onboarding1, name='onboarding1'),
    path('step2/', account_views.onboarding2, name='onboarding2'),
    path('step3/', account_views.onboarding3, name='onboarding3'),
    path('gate/', account_views.gate, name='gate'),

    # --- 会員登録フロー ---
    path('signup/', account_views.signup, name='signup'),
    
    # ★ ここが足りなかったためにエラーが出ていました
    path('verify/', account_views.verify_identity, name='verify_identity'), 
    path('verify/dob/', account_views.verify_dob, name='verify_dob'),
    path('profile-setup/', account_views.profile_setup, name='profile_setup'),

    # --- その他 ---
    path('login/', account_views.login_view, name='login'),
    path('home/', job_views.index, name='index'), # 登録完了後の「さがす」画面

     # jobsアプリ関連
    path('home/', job_views.index, name='index'),
    path('favorites/', job_views.favorites, name='favorites'),      # ★追加
    path('schedule/', job_views.work_schedule, name='work_schedule'), # ★追加
    path('messages/', job_views.messages, name='messages'),          # ★追加

    # accountsアプリ関連
    path('mypage/', account_views.mypage, name='mypage'),            # ★追加

    # 事業者登録フロー
    path('biz/', biz_views.landing, name='biz_landing'), # 画像3
    path('biz/signup/', biz_views.signup, name='biz_signup'), # 画像4, 5
    path('biz/account-register/', biz_views.account_register, name='biz_account_register'), # 追加
    path('biz/business-register/', biz_views.business_register, name='biz_business_register'), # 追加
    path('biz/verify/', biz_views.verify_docs, name='biz_verify'), # 画像6
    path('biz/store-setup/', biz_views.store_setup, name='biz_store_setup'), # 画像7
    path('biz/login/', biz_views.biz_login, name='biz_login'),
    
    # 事業者ダッシュボード
    path('biz/home/', biz_views.dashboard, name='biz_dashboard'), # 画像8, 9, 10

    # config/urls.py の urlpatterns 内に追加
    path('biz/templates/', biz_views.template_list, name='biz_template_list'),      # ひな形一覧
    path('biz/templates/create/', biz_views.template_create, name='biz_template_create'), # ひな形作成

    # 詳細画面
    path('biz/templates/<int:pk>/', biz_views.template_detail, name='biz_template_detail'),
    # 編集画面
    path('biz/templates/<int:pk>/edit/', biz_views.template_edit, name='biz_template_edit'),
    # このひな形を元に求人作成（勤務日時入力画面へ）
    path('biz/templates/<int:template_pk>/post/', biz_views.job_create_from_template, name='biz_job_create'),
    path('biz/job/confirm/', biz_views.job_confirm, name='biz_job_confirm'),
    path('biz/postings/', biz_views.job_posting_list, name='biz_job_posting_list'),
]