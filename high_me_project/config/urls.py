# config/urls.py

from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views
from jobs import views as job_views
from business import views as biz_views
from business import debug_views as debug_biz_views # Import debug view
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-portal/', include('administration.urls')),

    # --- オンボーディング ---
    path('', TemplateView.as_view(template_name='Auth/onboarding1.html'), name='onboarding1'),
    path('step2/', TemplateView.as_view(template_name='Auth/onboarding2.html'), name='onboarding2'),
    path('step3/', TemplateView.as_view(template_name='Auth/onboarding3.html'), name='onboarding3'),
    path('gate/', TemplateView.as_view(template_name='Auth/gate.html'), name='gate'),

    # --- 会員登録フロー ---
    # --- 会員登録フロー ---
    path('signup/', account_views.SignupView.as_view(), name='signup'),
    path('signup/name/', account_views.SetupNameView.as_view(), name='setup_name'),
    path('signup/kana/', account_views.SetupKanaView.as_view(), name='setup_kana'),
    path('signup/gender/', account_views.SetupGenderView.as_view(), name='setup_gender'),
    path('signup/photo/', account_views.SetupPhotoView.as_view(), name='setup_photo'),
    path('signup/address/', account_views.SetupAddressView.as_view(), name='setup_address'),
    path('signup/association/', account_views.SetupAssociationView.as_view(), name='setup_association'), # 新規追加
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
    path('working/completed/<int:pk>/', job_views.JobCompletedDetailView.as_view(), name='job_completed_detail'),
    path('working/<int:pk>/answer/', job_views.JobAnswerView.as_view(), name='job_answer'), # ★追加
    path('working/<int:pk>/qr/', job_views.QRScanView.as_view(), name='job_qr_scan'), # ★追加
    path('working/<int:pk>/reader/', job_views.JobQRReaderView.as_view(), name='job_qr_reader'),
    path('jobs/map/', job_views.MapSearchView.as_view(), name='map_search'),
    
    # 勤怠修正フロー
    path('attendance/<int:application_id>/step1/', job_views.AttendanceStep1CheckView.as_view(), name='attendance_step1'),
    path('attendance/<int:application_id>/step2/', job_views.AttendanceStep2GuideView.as_view(), name='attendance_step2'),
    path('attendance/<int:application_id>/step3/', job_views.AttendanceStep3TimeView.as_view(), name='attendance_step3'),
    path('attendance/<int:application_id>/step4/', job_views.AttendanceStep4BreakView.as_view(), name='attendance_step4'),
    path('attendance/<int:application_id>/step5/', job_views.AttendanceStep5LatenessView.as_view(), name='attendance_step5'),
    path('attendance/<int:application_id>/step6/', job_views.AttendanceStep6ConfirmView.as_view(), name='attendance_step6'),
    path('attendance/<int:application_id>/step7/', job_views.AttendanceStep7FinishView.as_view(), name='attendance_step7'),
    path('attendance/<int:application_id>/reward/', job_views.RewardConfirmView.as_view(), name='reward_confirm'), # ★追加
    path('attendance/<int:application_id>/finish/', job_views.RewardFinishView.as_view(), name='reward_finish'),   # ★追加
    path('attendance/<int:application_id>/status/', job_views.AttendanceCorrectionStatusView.as_view(), name='attendance_status'), # ★追加
    
    # 店舗評価
    path('work/application/<int:application_id>/review/step1/', job_views.StoreReviewStep1View.as_view(), name='store_review_step1'),
    path('work/application/<int:application_id>/review/step2/', job_views.StoreReviewStep2View.as_view(), name='store_review_step2'),
    path('work/application/<int:application_id>/review/complete/', job_views.StoreReviewCompleteView.as_view(), name='store_review_complete'),

    path('favorites/', job_views.FavoriteJobsView.as_view(), name='favorites'),      # ★変更
    path('favorites/stores/', job_views.FavoriteStoresView.as_view(), name='favorite_stores'), # ★追加
    path('schedule/', job_views.WorkScheduleUpcomingView.as_view(), name='work_schedule'), # ★変更
    path('schedule/completed/', job_views.WorkScheduleCompletedView.as_view(), name='work_completed'), # ★追加
    path('messages/', job_views.MessagesView.as_view(), name='messages'),          # ★追加
    path('home/refine/keyword/', job_views.KeywordExcludeView.as_view(), name='keyword_exclude'), # ★追加（NoReverseMatch対応）
    path('badges/', job_views.BadgeListView.as_view(), name='badge_list'),        # ★バッジ一覧
    path('badges/<int:pk>/', job_views.BadgeDetailView.as_view(), name='badge_detail'), # ★バッジ詳細
    
    # 店舗プロフィール & お気に入りAPI
    path('store/<int:store_id>/', job_views.StoreProfileView.as_view(), name='store_profile'),
    path('favorites/toggle/job/<int:job_id>/', job_views.ToggleFavoriteJobView.as_view(), name='toggle_favorite_job'),
    path('favorites/toggle/store/<int:store_id>/', job_views.ToggleFavoriteStoreView.as_view(), name='toggle_favorite_store'),

    # accountsアプリ関連
    path('mypage/', account_views.MypageView.as_view(), name='mypage'),            # ★追加
    path('mypage/credit/', account_views.CreditView.as_view(), name='credit'),     # ★新規追加
    path('mypage/grad-qna/', account_views.GraduationProjectQnAView.as_view(), name='grad_qna'), # ★新規追加
    # お問い合わせ
    path('support/inquiry/', account_views.InquiryView.as_view(), name='inquiry_form'),
    path('support/inquiry/complete/', account_views.InquiryCompleteView.as_view(), name='inquiry_complete'),
    path('support/faq/', account_views.FAQView.as_view(), name='faq'), # ★追加

    path('achievements/', account_views.AchievementsView.as_view(), name='achievements'), # ★実績画面追加
    path('past-jobs/', account_views.PastJobsView.as_view(), name='past_jobs'),   # ★これまでの仕事画面
    
    # 報酬管理 (ウォレット)
    path('rewards/', account_views.reward_management, name='reward_management'),
    path('rewards/history/', account_views.wallet_history, name='wallet_history'),
    path('rewards/bank-account/', account_views.bank_account_edit, name='bank_account_edit'),
    path('rewards/bank-account/create/', account_views.bank_account_create, name='bank_account_create'), # ★追加
    path('rewards/withdraw/', account_views.withdraw_application, name='withdraw_application'),
    path('rewards/withdraw/complete/', account_views.withdraw_complete, name='withdraw_complete'),
    
    # レビュー・ペナルティ
    path('rewards/reviews/', account_views.review_penalty, name='review_penalty'),
    path('rewards/penalty-detail/', account_views.ReviewPenaltyView.as_view(), name='penalty_detail'),
    path('taxes/annual/', account_views.AnnualTaxView.as_view(), name='annual_tax_list'), # ★追加
    path('taxes/slips/', account_views.TaxSlipView.as_view(), name='tax_slip_list'),   # ★追加
    path('rewards/earned/', account_views.EarnedRewardsView.as_view(), name='earned_rewards_list'), # ★追加

    # ワーカーメッセージ機能
    path('accounts/messages/', account_views.WorkerMessageListView.as_view(), name='worker_message_list'),
    path('accounts/messages/<int:room_id>/', account_views.WorkerMessageDetailView.as_view(), name='worker_message_detail'),

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
    path('settings/other/association/', account_views.association_select, name='association_select'), # ★所属選択画面
    path('settings/location/', account_views.LocationSettingsView.as_view(), name='location_settings'), # ★位置情報設定
    path('api/mute_store/', account_views.MuteStoreView.as_view(), name='api_mute_store'), # ★店舗ミュートAPI
    path('settings/muted_stores/', account_views.MutedStoresListView.as_view(), name='muted_stores_list'), # ★ミュート一覧
    path('api/unmute_store/', account_views.UnmuteStoreView.as_view(), name='api_unmute_store'), # ★ミュート解除API

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
    path('settings/workstyle/', account_views.workstyle_edit, name='workstyle_edit'), # ★働き方編集
    path('settings/phone/', account_views.phone_change_confirm, name='phone_change'),

    # 事業者登録フロー
    path('biz/', biz_views.LandingView.as_view(), name='biz_landing'),
    path('biz/materials/', biz_views.BizMaterialDownloadView.as_view(), name='biz_materials'),
    path('biz/content/', biz_views.BusinessContentView.as_view(), name='biz_content'),
    path('biz/settings/mail/', biz_views.BizMailSettingsView.as_view(), name='biz_mail_settings'),
    path('biz/signup/', biz_views.SignupView.as_view(), name='biz_signup'),
    path('biz/account-register/', biz_views.AccountRegisterView.as_view(), name='biz_account_register'),
    path('biz/business-register/', biz_views.BusinessRegisterView.as_view(), name='biz_business_register'),
    path('biz/verify/', biz_views.VerifyDocsView.as_view(), name='biz_verify'),
    path('biz/store-setup/', biz_views.StoreSetupView.as_view(), name='biz_store_setup'),
    path('biz/complete/', biz_views.SignupCompleteView.as_view(), name='biz_signup_complete'),
    # --- 登録・ログイン ---
    path('biz/login/', biz_views.BizLoginView.as_view(), name='biz_login'),
    path('biz/password-reset/', biz_views.BizPasswordResetRequestView.as_view(), name='biz_password_reset_request'),
    path('biz/password-reset/confirm/', biz_views.BizPasswordResetView.as_view(), name='biz_password_reset_confirm'),
    # --- 企業用マイページ ---
    path('biz/portal/', biz_views.BizPortalView.as_view(), name='biz_portal'),
    path('biz/account-info/', biz_views.BizAccountInfoView.as_view(), name='biz_account_info'),
    path('biz/account-info/basic/edit/', biz_views.BizBasicInfoEditView.as_view(), name='biz_basic_info_edit'),

    # 事業者ダッシュボード
    path('biz/store/<int:store_id>/home/', biz_views.DashboardView.as_view(), name='biz_dashboard'),
    path('biz/store/<int:store_id>/templates/', biz_views.TemplateListView.as_view(), name='biz_template_list'),
    path('biz/store/<int:store_id>/templates/create/', biz_views.TemplateCreateView.as_view(), name='biz_template_create'),
    path('biz/store/<int:store_id>/templates/confirm/', biz_views.TemplateConfirmView.as_view(), name='biz_template_confirm'),
    path('biz/store/<int:store_id>/templates/complete/', biz_views.TemplateCompleteView.as_view(), name='biz_template_complete'),

    # --- 店舗追加機能 ---
    path('biz/simple-create/', biz_views.SimpleStoreCreateView.as_view(), name='biz_simple_create'),
    # path('biz/creation/new-store/', biz_views.AddStoreView.as_view(), name='biz_add_store'),

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
    # ワーカー詳細(店舗向け)
    # ワーカー関連
    path('biz/store/<int:store_id>/workers/', biz_views.BizWorkerManagementView.as_view(), name='biz_worker_management'),
    path('biz/store/<int:store_id>/workers/<int:worker_id>/', biz_views.JobWorkerDetailView.as_view(), name='biz_worker_detail'),
    path('biz/store/<int:store_id>/groups/', biz_views.BizGroupManagementView.as_view(), name='biz_group_management'),
    path('biz/store/<int:store_id>/reviews/', biz_views.BizWorkerReviewJobListView.as_view(), name='biz_worker_review_job_list'),
    path('biz/store/<int:store_id>/reviews/<int:job_id>/', biz_views.BizWorkerReviewListView.as_view(), name='biz_worker_review_list'),
    path('biz/workers/review/submit/<int:store_id>/', biz_views.BizWorkerReviewSubmitView.as_view(), name='biz_worker_review_submit'),
    path('biz/workers/review/complete/<int:store_id>/', biz_views.BizReviewCompleteView.as_view(), name='biz_review_complete'),

    # メッセージ機能
    # メッセージ機能
    path('biz/store/<int:store_id>/messages/', biz_views.BizMessageListView.as_view(), name='biz_message_list'),
    path('biz/messages/<int:room_id>/', biz_views.BizMessageDetailView.as_view(), name='biz_message_detail'),
    
    # チェックイン/アウト管理 (店舗QR表示)
    path('biz/checkin-management/', biz_views.BizCheckinManagementView.as_view(), name='biz_checkin_management'), 

    # お問い合わせ
    path('biz/support/inquiry/', biz_views.BizInquiryView.as_view(), name='biz_inquiry'),
    path('biz/support/inquiry/complete/', biz_views.BizInquiryCompleteView.as_view(), name='biz_inquiry_complete'), 

    # 勤怠修正依頼 (店舗承認フロー)
    path('biz/store/<int:store_id>/corrections/', biz_views.AttendanceCorrectionListView.as_view(), name='biz_attendance_correction_list'),
    path('biz/store/<int:store_id>/corrections/<int:pk>/', biz_views.AttendanceCorrectionDetailView.as_view(), name='biz_attendance_correction_detail'),
    
    # 年間報酬による制限の解除
    path('biz/limit/release/', biz_views.AnnualLimitReleaseView.as_view(), name='biz_limit_release'),
    path('biz/limit/release/confirm/', biz_views.AnnualLimitReleaseConfirmView.as_view(), name='biz_limit_release_confirm'),
    path('biz/limit/release/finish/', biz_views.AnnualLimitReleaseFinishView.as_view(), name='biz_limit_release_finish'),

    # 店舗レビュー
    path('biz/store/<int:store_id>/store-reviews/', biz_views.StoreReviewListView.as_view(), name='biz_store_reviews'),
    
    # 求人詳細画面
    # 求人詳細画面
    path('job/<int:pk>/', job_views.JobDetailView.as_view(), name='job_detail'),
    # 申込画面一連フロー
    path('job/<int:pk>/apply/belongings/', job_views.ApplyStep1BelongingsView.as_view(), name='apply_step_1'),
    path('job/<int:pk>/apply/conditions/', job_views.ApplyStep2ConditionsView.as_view(), name='apply_step_2_conditions'),
    path('job/<int:pk>/apply/documents/', job_views.ApplyStep3DocumentsView.as_view(), name='apply_step_3_documents'),
    path('job/<int:pk>/apply/policy/', job_views.ApplyStep4PolicyView.as_view(), name='apply_step_4_policy'),
    path('job/<int:pk>/apply/review/', job_views.ApplyStep5ReviewView.as_view(), name='apply_step_5_review'),
    
    # キャンセル機能
    path('working/<int:application_id>/cancel/step1/', job_views.JobCancelStep1PenaltyView.as_view(), name='job_cancel_step1'),
    path('working/<int:application_id>/cancel/step2/', job_views.JobCancelStep2ReasonView.as_view(), name='job_cancel_step2'),
    path('working/<int:application_id>/cancel/step3/', job_views.JobCancelStep3DetailView.as_view(), name='job_cancel_step3'),
    path('working/<int:application_id>/cancel/step4/', job_views.JobCancelStep4InputView.as_view(), name='job_cancel_step4'),
    
    # 長期バイト応募履歴
    path('working/long-term/', job_views.LongTermJobHistoryView.as_view(), name='work_history_long_term'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)