# config/urls.py

from django.contrib import admin
from django.urls import path
from accounts import views as account_views
from jobs import views as job_views
from business import views as biz_views
from django.conf import settings
from django.conf.urls.static import static

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
    # 場所フロー
    path('home/location/', job_views.location_home, name='location_home'),
    path('home/location/prefs/', job_views.pref_select, name='pref_select'),
    path('home/location/map/', job_views.map_view, name='map_view'),
    # 絞り込みフロー
    path('home/refine/', job_views.refine_home, name='refine_home'),
    path('home/refine/occupation/', job_views.occupation_select, name='occupation_select'),
    path('home/refine/reward/', job_views.reward_select, name='reward_select'),

    # ★ ここから下の3行が不足していたためエラーになっていました
    path('home/refine/time/', job_views.time_select, name='time_select'),
    path('home/refine/treatment/', job_views.treatment_select, name='treatment_select'),
    path('home/refine/keyword/', job_views.keyword_exclude, name='keyword_exclude'),

    path('favorites/', job_views.favorites, name='favorites'),      # ★追加
    path('schedule/', job_views.work_schedule, name='work_schedule'), # ★追加
    path('messages/', job_views.messages, name='messages'),          # ★追加

    # accountsアプリ関連
    path('mypage/', account_views.mypage, name='mypage'),            # ★追加
    path('settings/', account_views.account_settings, name='account_settings'), # 設定一覧
    path('settings/profile/', account_views.profile_edit, name='profile_edit'), # ★プロフィール編集画面
    path('settings/other/', account_views.other_profile_edit, name='other_profile_edit'),

    # 修正：phone_change_home を phone_change に変更
    # 電話番号変更フロー
    # 1. 現在の番号表示画面
    path('settings/phone/', account_views.phone_change, name='phone_change'), 
    
    # 2. 登録済み番号の入力画面 (ここを phone_verify_old に統一します)
    path('settings/phone/verify-old/', account_views.phone_change_confirm, name='phone_verify_old'), 
    
    # 3. 新しい番号の入力画面
    path('settings/phone/new/', account_views.phone_input_new, name='phone_input_new'), 
    
    # 4. パスワード確定画面
    path('settings/phone/confirm/', account_views.phone_confirm_password, name='phone_confirm_password'),

    # アカウント設定関連
    path('settings/', account_views.account_settings, name='account_settings'),
    path('settings/profile/', account_views.profile_edit, name='profile_edit'),
    path('settings/emergency/', account_views.emergency_contact_edit, name='emergency_contact'),
    path('settings/phone/', account_views.phone_change_confirm, name='phone_change'),

    # 事業者登録フロー
    path('biz/', biz_views.landing, name='biz_landing'), # 画像3
    path('biz/signup/', biz_views.signup, name='biz_signup'), # 画像4, 5
    path('biz/account-register/', biz_views.account_register, name='biz_account_register'), # 追加
    path('biz/business-register/', biz_views.business_register, name='biz_business_register'), # 追加
    path('biz/verify/', biz_views.verify_docs, name='biz_verify'), # 画像6
    path('biz/store-setup/', biz_views.store_setup, name='biz_store_setup'), # 画像7
    # --- 登録・ログイン ---
    path('biz/login/', biz_views.biz_login, name='biz_login'),
    # --- 企業用マイページ（画像1：企業・店舗一覧） ---
    path('biz/portal/', biz_views.biz_portal, name='biz_portal'),

    
    # 事業者ダッシュボード
    # --- 各店舗ごとの管理画面（URLにIDを入れる） ---
    path('biz/store/<int:store_id>/home/', biz_views.dashboard, name='biz_dashboard'),
    path('biz/store/<int:store_id>/templates/', biz_views.template_list, name='biz_template_list'),
    path('biz/store/<int:store_id>/templates/create/', biz_views.template_create, name='biz_template_create'),

    # config/urls.py の urlpatterns 内に追加
    path('biz/templates/', biz_views.template_list, name='biz_template_list'),      # ひな形一覧
   path('biz/store/<int:store_id>/templates/create/', biz_views.template_create, name='biz_template_create'),

    # --- 店舗追加機能 ---
    path('biz/portal/add-store/', biz_views.add_store, name='biz_add_store'),

    # 詳細画面
    path('biz/templates/<int:pk>/', biz_views.template_detail, name='biz_template_detail'),
    # 編集画面
    path('biz/templates/<int:pk>/edit/', biz_views.template_edit, name='biz_template_edit'),
    # このひな形を元に求人作成（勤務日時入力画面へ）
    path('biz/templates/<int:template_pk>/post/', biz_views.job_create_from_template, name='biz_job_create'),
    path('biz/job/confirm/', biz_views.job_confirm, name='biz_job_confirm'),
    path('biz/store/<int:store_id>/postings/', biz_views.job_posting_list, name='biz_job_posting_list'),

    # 求人詳細画面
    path('job/<int:pk>/', job_views.job_detail, name='job_detail'),
    # 申込画面一連フロー
    path('job/<int:pk>/apply/belongings/', job_views.apply_step_1_belongings, name='apply_step_1'),
    path('job/<int:pk>/apply/conditions/', job_views.apply_step_2_conditions, name='apply_step_2_conditions'), # 修正
    path('job/<int:pk>/apply/documents/', job_views.apply_step_3_documents, name='apply_step_3_documents'),   # 修正
    path('job/<int:pk>/apply/policy/', job_views.apply_step_4_policy, name='apply_step_4_policy'),             # 修正
    path('job/<int:pk>/apply/review/', job_views.apply_step_5_review, name='apply_step_5_review'),             # 修正
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)