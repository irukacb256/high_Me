from django.shortcuts import render , get_object_or_404
from business.models import JobPosting
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q

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
    
    postings = JobPosting.objects.filter(is_published=True, work_date=selected_date)
    if selected_prefs:
        postings = postings.filter(template__store__prefecture__in=selected_prefs)
    
    context = {
        'date_list': [timezone.now().date() + timedelta(days=i) for i in range(14)],
        'selected_date': selected_date,
        'main_jobs': postings,
        'selected_prefs': selected_prefs,
        'today': timezone.now().date(),
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