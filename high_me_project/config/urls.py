# config/urls.py

from django.contrib import admin
from django.urls import path
from accounts import views as account_views
from jobs import views as job_views
from business import views as biz_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- オンボーディング ---
    path('', TemplateView.as_view(template_name='accounts/onboarding1.html'), name='onboarding1'),
    path('step2/', TemplateView.as_view(template_name='accounts/onboarding2.html'), name='onboarding2'),
    path('step3/', TemplateView.as_view(template_name='accounts/onboarding3.html'), name='onboarding3'),
    path('gate/', TemplateView.as_view(template_name='accounts/gate.html'), name='gate'),

    # --- 会員登録フロー ---
    # --- 会員登録フロー ---
    path('signup/', account_views.SignupView.as_view(), name='signup'),
    path('signup/name/', account_views.SetupNameView.as_view(), name='setup_name'),
    path('signup/kana/', account_views.SetupKanaView.as_view(), name='setup_kana'),
    path('signup/gender/', account_views.SetupGenderView.as_view(), name='setup_gender'),
    path('signup/photo/', account_views.SetupPhotoView.as_view(), name='setup_photo'),
    path('signup/address/', account_views.SetupAddressView.as_view(), name='setup_address'),
    path('signup/workstyle/', account_views.SetupWorkstyleView.as_view(), name='setup_workstyle'),
    path('signup/pref-select/', account_views.SetupPrefSelectView.as_view(), name='setup_pref_select'),
    
    # 新規本人確認フロー (サインアップ用)
    path('signup/identity/', account_views.SignupVerifyIdentityView.as_view(), name='signup_verify_identity'),
    path('signup/identity/skip/', account_views.signup_verify_identity_skip, name='signup_verify_identity_skip'),
    path('signup/confirm/', account_views.SignupConfirmView.as_view(), name='signup_confirm'),
    
    # ★ ここが足りなかったためにエラーが出ていました
    path('verify/', account_views.verify_identity, name='verify_identity'), 
    path('verify/select/', account_views.VerifyIdentitySelectView.as_view(), name='verify_identity_select'), 
    path('verify/upload/', account_views.VerifyIdentityUploadView.as_view(), name='verify_identity_upload'), 
    path('verify/dob/', account_views.VerifyDobView.as_view(), name='verify_dob'),
    path('profile-setup/', account_views.profile_setup, name='profile_setup'),

    # --- その他 ---
    path('login/', account_views.CustomLoginView.as_view(), name='login'),
    # path('home/', job_views.index, name='index'), # 登録完了後の「さがす」画面

      # jobsアプリ関連
    path('home/', job_views.IndexView.as_view(), name='index'),
    # 場所フロー
    path('home/location/', job_views.LocationHomeView.as_view(), name='location_home'),
    path('home/location/prefs/', job_views.PrefSelectView.as_view(), name='pref_select'),
    path('home/location/map/', job_views.MapView.as_view(), name='map_view'),
    # 絞り込みフロー
    path('home/refine/', job_views.RefineHomeView.as_view(), name='refine_home'),
    path('home/refine/occupation/', job_views.OccupationSelectView.as_view(), name='occupation_select'),
    path('home/refine/reward/', job_views.RewardSelectView.as_view(), name='reward_select'),

    # ★ ここから下の3行が不足していたためエラーになっていました
    path('home/refine/time/', job_views.TimeSelectView.as_view(), name='time_select'),
    path('home/refine/treatment/', job_views.TreatmentSelectView.as_view(), name='treatment_select'),
    path('working/<int:pk>/', job_views.JobWorkingDetailView.as_view(), name='job_working_detail'),
    path('favorites/', job_views.FavoritesView.as_view(), name='favorites'),      # ★追加
    path('schedule/', job_views.WorkScheduleView.as_view(), name='work_schedule'), # ★追加
    path('messages/', job_views.MessagesView.as_view(), name='messages'),          # ★追加
    path('home/refine/keyword/', job_views.KeywordExcludeView.as_view(), name='keyword_exclude'), # ★追加（NoReverseMatch対応）
    path('badges/', job_views.BadgeListView.as_view(), name='badge_list'),        # ★バッジ一覧
    
    # 店舗プロフィール & お気に入りAPI
    path('store/<int:store_id>/', job_views.StoreProfileView.as_view(), name='store_profile'),
    path('favorites/toggle/job/<int:job_id>/', job_views.ToggleFavoriteJobView.as_view(), name='toggle_favorite_job'),
    path('favorites/toggle/store/<int:store_id>/', job_views.ToggleFavoriteStoreView.as_view(), name='toggle_favorite_store'),

    # accountsアプリ関連
    path('mypage/', account_views.MypageView.as_view(), name='mypage'),            # ★追加
    path('achievements/', account_views.AchievementsView.as_view(), name='achievements'), # ★実績画面追加
    path('past-jobs/', account_views.PastJobsView.as_view(), name='past_jobs'),   # ★これまでの仕事画面
    
    # 報酬管理 (ウォレット)
    path('rewards/', account_views.reward_management, name='reward_management'),
    path('rewards/history/', account_views.wallet_history, name='wallet_history'),
    path('rewards/bank-account/', account_views.bank_account_edit, name='bank_account_edit'),
    path('rewards/withdraw/', account_views.withdraw_application, name='withdraw_application'),
    
    # レビュー・ペナルティ
    path('rewards/reviews/', account_views.review_penalty, name='review_penalty'),
    path('rewards/penalty-detail/', account_views.penalty_detail, name='penalty_detail'),

    # 保有資格
    path('qualifications/', account_views.qualification_list, name='qualification_list'),
    path('qualifications/create/', account_views.qualification_create, name='qualification_create'),
    path('qualifications/upload/', account_views.qualification_photo_upload, name='qualification_photo_upload'),
    path('qualifications/confirm/', account_views.qualification_photo_confirm, name='qualification_photo_confirm'),
    path('qualifications/categories/', account_views.qualification_category_select, name='qualification_category_select'),
    path('qualifications/categories/<int:category_id>/items/', account_views.qualification_item_select, name='qualification_item_select'),

    path('settings/', account_views.account_settings, name='account_settings'), # 設定一覧
    path('settings/profile/', account_views.profile_edit, name='profile_edit'), # ★プロフィール編集画面
    path('settings/profile/address/', account_views.profile_address_edit, name='profile_address_edit'), # ★住所変更専用画面
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
    path('biz/', biz_views.LandingView.as_view(), name='biz_landing'),
    path('biz/signup/', biz_views.SignupView.as_view(), name='biz_signup'),
    path('biz/account-register/', biz_views.AccountRegisterView.as_view(), name='biz_account_register'),
    path('biz/business-register/', biz_views.BusinessRegisterView.as_view(), name='biz_business_register'),
    path('biz/verify/', biz_views.VerifyDocsView.as_view(), name='biz_verify'),
    path('biz/store-setup/', biz_views.StoreSetupView.as_view(), name='biz_store_setup'),
    path('biz/complete/', biz_views.SignupCompleteView.as_view(), name='biz_signup_complete'),
    # --- 登録・ログイン ---
    path('biz/login/', biz_views.BizLoginView.as_view(), name='biz_login'),
    path('biz/password-reset/', biz_views.BizPasswordResetView.as_view(), name='biz_password_reset'),
    # --- 企業用マイページ ---
    path('biz/portal/', biz_views.BizPortalView.as_view(), name='biz_portal'),

    # 事業者ダッシュボード
    path('biz/store/<int:store_id>/home/', biz_views.DashboardView.as_view(), name='biz_dashboard'),
    path('biz/store/<int:store_id>/templates/', biz_views.TemplateListView.as_view(), name='biz_template_list'),
    path('biz/store/<int:store_id>/templates/create/', biz_views.TemplateCreateView.as_view(), name='biz_template_create'),

    # --- 店舗追加機能 ---
    path('biz/portal/add-store/', biz_views.AddStoreView.as_view(), name='biz_add_store'),

    # 詳細画面
    path('biz/templates/<int:pk>/', biz_views.TemplateDetailView.as_view(), name='biz_template_detail'),
    # 編集画面
    path('biz/templates/<int:pk>/edit/', biz_views.TemplateUpdateView.as_view(), name='biz_template_edit'),
    # 削除画面
    path('biz/templates/<int:pk>/delete/', biz_views.TemplateDeleteView.as_view(), name='biz_template_delete'),
    # このひな形を元に求人作成
    path('biz/templates/<int:template_pk>/post/', biz_views.JobCreateFromTemplateView.as_view(), name='biz_job_create'),
    path('biz/job/<int:store_id>/<int:pk>/visibility/', biz_views.JobPostingVisibilityEditView.as_view(), name='biz_job_visibility_edit'),
    path('biz/job/confirm/', biz_views.JobConfirmView.as_view(), name='biz_job_confirm'),
    path('biz/store/<int:store_id>/postings/', biz_views.JobPostingListView.as_view(), name='biz_job_posting_list'),
    path('biz/store/<int:store_id>/postings/<int:pk>/', biz_views.JobPostingDetailView.as_view(), name='biz_job_posting_detail'),
    #ワーカーの確認
    path('biz/store/<int:store_id>/postings/<int:pk>/workers/', biz_views.JobWorkerListView.as_view(), name='biz_job_worker_list'),
    # ワーカー詳細(店舗向け)
    path('biz/store/<int:store_id>/workers/<int:worker_id>/', biz_views.JobWorkerDetailView.as_view(), name='biz_worker_detail'),

    # 求人詳細画面
    # 求人詳細画面
    path('job/<int:pk>/', job_views.JobDetailView.as_view(), name='job_detail'),
    # 申込画面一連フロー
    path('job/<int:pk>/apply/belongings/', job_views.ApplyStep1BelongingsView.as_view(), name='apply_step_1'),
    path('job/<int:pk>/apply/conditions/', job_views.ApplyStep2ConditionsView.as_view(), name='apply_step_2_conditions'),
    path('job/<int:pk>/apply/documents/', job_views.ApplyStep3DocumentsView.as_view(), name='apply_step_3_documents'),
    path('job/<int:pk>/apply/policy/', job_views.ApplyStep4PolicyView.as_view(), name='apply_step_4_policy'),
    path('job/<int:pk>/apply/review/', job_views.ApplyStep5ReviewView.as_view(), name='apply_step_5_review'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)