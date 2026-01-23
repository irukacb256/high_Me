from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from business.models import JobPosting, JobApplication, Store
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q
from .models import FavoriteJob, FavoriteStore
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# 共通データ
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]
OCCUPATIONS = ["軽作業", "飲食", "介護", "配達・運転", "販売", "オフィスワーク", "接客", "エンタメ"]
REWARDS = [3000, 5000, 8000, 10000]

def index(request):
    """メイン：さがす画面"""
    date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    selected_prefs = request.GET.getlist('pref')
    
    postings = JobPosting.objects.filter(is_published=True, work_date=selected_date).prefetch_related('template__photos')
    if selected_prefs:
        postings = postings.filter(template__store__prefecture__in=selected_prefs)
    
    # お気に入り状況取得
    user_fav_job_ids = []
    if request.user.is_authenticated:
        user_fav_job_ids = FavoriteJob.objects.filter(user=request.user).values_list('job_posting_id', flat=True)
    
    context = {
        'date_list': [timezone.now().date() + timedelta(days=i) for i in range(14)],
        'selected_date': selected_date,
        'main_jobs': postings,
        'selected_prefs': selected_prefs,
        'today': timezone.now().date(),
        'user_fav_job_ids': set(user_fav_job_ids),
    }
    return render(request, 'jobs/index.html', context)

# --- 場所フロー ---
def location_home(request):
    """画像5左：場所の設定トップ"""
    selected_prefs = request.GET.getlist('pref')
    return render(request, 'jobs/location_home.html', {'selected_prefs': selected_prefs})

def pref_select(request):
    """画像5中：都道府県リスト"""
    selected_prefs = request.GET.getlist('pref')
    return render(request, 'jobs/pref_select.html', {
        'prefectures_list': PREFECTURES,
        'selected_prefs': selected_prefs
    })

def map_view(request):
    """画像5右：全画面マップ (エラーの箇所)"""
    return render(request, 'jobs/map_view.html')

# --- 絞り込みフロー ---
def refine_home(request):
    """画像3左：絞り込みメイン"""
    return render(request, 'jobs/refine_home.html')

def time_select(request):
    """画像2左：時間帯を選択"""
    return render(request, 'jobs/time_select.html')

def treatment_select(request):
    """画像2中：待遇を選択"""
    treatment_list = ["未経験者歓迎", "バイク/車通勤可", "服装自由", "クーポンGET", "まかないあり", "髪型/カラー自由", "交通費支給"]
    return render(request, 'jobs/treatment_select.html', {'treatment_list': treatment_list})

def keyword_exclude(request):
    """画像2右：除外キーワード"""
    return render(request, 'jobs/keyword_exclude.html')

def occupation_select(request):
    """画像3中：職種選択"""
    return render(request, 'jobs/occupation_select.html', {'occupation_list': OCCUPATIONS})

def reward_select(request):
    """画像3右：報酬選択"""
    return render(request, 'jobs/reward_select.html', {'reward_list': REWARDS})

def job_detail(request, pk):
    """求人詳細画面 (画像2)"""
    job = get_object_or_404(JobPosting.objects.prefetch_related('template__photos'), pk=pk)
    is_applied = False
    is_favorited = False
    if request.user.is_authenticated:
        is_applied = JobApplication.objects.filter(job_posting=job, worker=request.user).exists()
        is_favorited = FavoriteJob.objects.filter(user=request.user, job_posting=job).exists()
    
    return render(request, 'jobs/detail.html', {
        'job': job, 
        'is_applied': is_applied,
        'is_favorited': is_favorited,
        'is_closed': job.is_expired
    })

@login_required
def favorites(request):
    """お気に入り画面 (画像2)"""
    # お気に入り求人を取得
    favorite_jobs = FavoriteJob.objects.filter(user=request.user).select_related('job_posting', 'job_posting__template__store').order_by('-created_at')
    
    # お気に入り店舗を取得
    favorite_stores = FavoriteStore.objects.filter(user=request.user).select_related('store').order_by('-created_at')
    
    context = {
        'favorite_jobs': favorite_jobs,
        'favorite_stores': favorite_stores,
        'tab': request.GET.get('tab', 'jobs') # 'jobs' or 'stores'
    }
    return render(request, 'jobs/favorites.html', context)

@login_required
def store_profile(request, store_id):
    """店舗プロフィール画面"""
    store = get_object_or_404(Store, id=store_id)
    
    # この店舗の求人一覧（期限切れでないもの）
    job_postings = JobPosting.objects.filter(
        template__store=store,
        work_date__gte=timezone.now().date()
    ).order_by('work_date', 'start_time')
    
    # お気に入り済みかどうか
    is_favorited = FavoriteStore.objects.filter(user=request.user, store=store).exists()
    
    # 求人リストにお気に入り情報を付加
    # (詳細なN+1対策は割愛するが、本来はPrefetchなどを利用)
    user_fav_job_ids = FavoriteJob.objects.filter(user=request.user).values_list('job_posting_id', flat=True)

    return render(request, 'jobs/store_profile.html', {
        'store': store,
        'job_postings': job_postings,
        'is_favorited': is_favorited,
        'user_fav_job_ids': set(user_fav_job_ids),
    })

@login_required
@require_POST
def toggle_favorite_job(request, job_id):
    """求人お気に入りトグルAPI"""
    job = get_object_or_404(JobPosting, id=job_id)
    fav_job, created = FavoriteJob.objects.get_or_create(user=request.user, job_posting=job)
    
    if not created:
        # 既に存在していた場合は削除（トグル動作）
        fav_job.delete()
        is_favorited = False
    else:
        is_favorited = True
        
    return JsonResponse({'status': 'success', 'is_favorited': is_favorited})

@login_required
@require_POST
def toggle_favorite_store(request, store_id):
    """店舗お気に入りトグルAPI"""
    store = get_object_or_404(Store, id=store_id)
    fav_store, created = FavoriteStore.objects.get_or_create(user=request.user, store=store)
    
    if not created:
        fav_store.delete()
        is_favorited = False
    else:
        is_favorited = True
        
    return JsonResponse({'status': 'success', 'is_favorited': is_favorited})

@login_required
def work_schedule(request):
    """はたらく画面 (画像3)"""
    now = timezone.now()
    # ユーザーの応募済み求人を全て取得（勤務日の昇順）
    applications = JobApplication.objects.filter(worker=request.user).select_related('job_posting', 'job_posting__template__store').order_by('job_posting__work_date', 'job_posting__start_time')
    
    upcoming = []
    completed = []
    
    for app in applications:
        # 終了時間を考慮した完了判定（簡易的に勤務日と終了時間で判定）
        job_end = timezone.make_aware(datetime.combine(app.job_posting.work_date, app.job_posting.end_time))
        if job_end < now:
            completed.append(app)
        else:
            upcoming.append(app)

    # 日付ごとにグルーピングする関数（テンプレート用）
    def group_by_date(app_list):
        grouped = {}
        # 曜日変換マップ
        weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        for app in app_list:
            d = app.job_posting.work_date
            if d not in grouped:
                # (曜日(JP), アプリリスト)
                grouped[d] = [weekday_map[d.weekday()], []]
            grouped[d][1].append(app)
        
        # [(date, weekday_jp, [apps]), ...] の形式でソートして返す
        result = []
        for d in sorted(grouped.keys()):
            result.append((d, grouped[d][0], grouped[d][1]))
        return result

    context = {
        'upcoming_grouped': group_by_date(upcoming),
        'completed_grouped': group_by_date(completed),
        'tab': request.GET.get('tab', 'upcoming'),
    }
    return render(request, 'jobs/work_schedule.html', context)

def messages(request):
    """メッセージ画面 (画像4)"""
    return render(request, 'jobs/messages.html')


@login_required
def apply_step_1_belongings(request, pk):
    """ステップ1: 持ち物確認 (画像4)"""
    job = get_object_or_404(JobPosting, pk=pk)
    profile = request.user.workerprofile

    # シーケンス図代替フロー: 本人確認をしていない場合
    if not profile.is_identity_verified:
        return render(request, 'jobs/detail.html', {'job': job, 'needs_verification': True})

    # シーケンス図代替フロー: 求人が締切済み/満員の場合
    if job.is_expired: # 前回定義したプロパティ
        return render(request, 'jobs/detail.html', {'job': job, 'is_closed': True})

    if request.method == 'POST':
        return redirect('apply_step_2_conditions', pk=pk)
    
    return render(request, 'jobs/apply_belongings.html', {'job': job})

@login_required
def apply_step_2_conditions(request, pk):
    """ステップ2: 働くための条件確認 (画像5)"""
    job = get_object_or_404(JobPosting, pk=pk)
    if request.method == 'POST':
        return redirect('apply_step_3_documents', pk=pk)
    return render(request, 'jobs/apply_conditions.html', {'job': job})

@login_required
def apply_step_3_documents(request, pk):
    """ステップ3: 業務に関する書類確認 (画像6)"""
    job = get_object_or_404(JobPosting, pk=pk)
    if request.method == 'POST':
        return redirect('apply_step_4_policy', pk=pk)
    return render(request, 'jobs/apply_documents.html', {'job': job})

@login_required
def job_working_detail(request, pk):
    """おしごと画面 (申し込み後の詳細・チェックイン)"""
    application = get_object_or_404(JobApplication, job_posting_id=pk, worker=request.user)
    # 曜日マップ（再利用）
    weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
    weekday_jp = weekday_map[application.job_posting.work_date.weekday()]
    
    return render(request, 'jobs/job_working_detail.html', {
        'app': application,
        'weekday_jp': weekday_jp
    })

@login_required
def apply_step_4_policy(request, pk):
    """ステップ4: キャンセルポリシー同意 (画像7, 8)"""
    job = get_object_or_404(JobPosting, pk=pk)
    if request.method == 'POST':
        return redirect('apply_step_5_review', pk=pk)
    return render(request, 'jobs/apply_policy.html', {'job': job})

@login_required
def apply_step_5_review(request, pk):
    """ステップ5: 申し込み内容の最終確認"""
    job = get_object_or_404(JobPosting, pk=pk)
    
    if request.method == 'POST':
        # --- ここで実際の申し込みデータを保存する ---
        # 重複申し込みを防ぎつつ作成
        application, created = JobApplication.objects.get_or_create(
            job_posting=job,
            worker=request.user
        )
        # ---------------------------------------
        return render(request, 'jobs/apply_complete.html', {'job': job})
    
    return render(request, 'jobs/apply_review.html', {'job': job})

@login_required
def badge_list(request):
    """バッジ一覧画面"""
    from accounts.models import Badge, WorkerBadge  # ここでインポート（循環参照回避のため）

    badges = Badge.objects.all()
    # ログインユーザーのバッジ獲得状況を取得
    my_badges = WorkerBadge.objects.filter(worker=request.user.workerprofile).select_related('badge')
    
    # バッジIDをキーにした辞書を作成（テンプレートで引きやすくするため）
    my_badges_dict = {wb.badge.id: wb for wb in my_badges}

    return render(request, 'jobs/badge_list.html', {
        'badges': badges,
        'my_badges_dict': my_badges_dict,
    })
