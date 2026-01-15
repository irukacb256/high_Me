from django.shortcuts import render , get_object_or_404
from business.models import JobPosting
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q

def index(request):
    """ワーカー側：さがす（仕事一覧）画面"""
    # 1. 現在時刻と日付の取得
    now = timezone.now()
    today = now.date()
    current_time = now.time()

    # 2. 都道府県リスト（View側で用意してsplitエラーを回避）
    prefectures_list = [
        "東京都", "神奈川県", "埼玉県", "千葉県", "宮城県", 
        "愛知県", "大阪府", "京都府", "兵庫県", "福岡県"
    ]
    reward_list = [3000, 5000, 8000, 10000] # ★これを追加

    # 3. リクエストパラメータの取得
    date_str = request.GET.get('date')
    selected_prefs = request.GET.getlist('pref')      # 複数選択対応
    min_reward = request.GET.get('reward')           # 報酬絞り込み
    
    # 日付の設定（指定がなければ今日）
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # 4. 求人データの取得とフィルタリング
    # 基本条件：公開中 かつ 選択された日付
    postings = JobPosting.objects.filter(is_published=True, work_date=selected_date)

    # 今日の場合は、開始時刻を過ぎたものは自動で除外（自動締切ロジック）
    if selected_date == today:
        postings = postings.filter(start_time__gt=current_time)

    # 都道府県で絞り込み
    if selected_prefs:
        postings = postings.filter(template__store__prefecture__in=selected_prefs)

    # 報酬で絞り込み（Python側で計算・フィルタリング）
    if min_reward:
        min_amount = int(min_reward)
        postings = [p for p in postings if p.total_payment >= min_amount]

    # 5. 今日から14日分の日付リスト作成
    date_list = [today + timedelta(days=i) for i in range(14)]

    context = {
        'date_list': date_list,
        'selected_date': selected_date,
        'main_jobs': postings,
        'today': today,
        'reward_list': reward_list, # ★これを追加
        'prefectures_list': prefectures_list,
        'selected_prefs': selected_prefs,
        'selected_reward': min_reward,
    }
    return render(request, 'jobs/index.html', context)

def job_detail(request, pk):
    """求人詳細画面 (画像2)"""
    job = get_object_or_404(JobPosting, pk=pk)
    return render(request, 'jobs/detail.html', {'job': job})

def favorites(request):
    """お気に入り画面 (画像2)"""
    return render(request, 'jobs/favorites.html')

def work_schedule(request):
    """はたらく画面 (画像3)"""
    return render(request, 'jobs/work_schedule.html')

def messages(request):
    """メッセージ画面 (画像4)"""
    return render(request, 'jobs/messages.html')