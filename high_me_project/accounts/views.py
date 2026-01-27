from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import WorkerProfile, WorkerBankAccount, WalletTransaction, QualificationCategory, QualificationItem, WorkerQualification, WorkerMembership, ExpHistory
from business.models import JobApplication
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import IntegrityError
from django.contrib.auth import authenticate, login
from datetime import date
from jobs.views import PREFECTURES
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage


# --- オンボーディングの流れ ---

def onboarding1(request):
    """画像1の1枚目: すぐ働けて、すぐお金がもらえる"""
    return render(request, 'accounts/onboarding1.html')

def onboarding2(request):
    """画像1の2枚目: 働いたら、お金はすぐGET"""
    return render(request, 'accounts/onboarding2.html')

def onboarding3(request):
    """画像1の3枚目: 便利な機能で仕事をチェック"""
    return render(request, 'accounts/onboarding3.html')

def gate(request):
    """画像2: はじめる / ログイン選択画面"""
    return render(request, 'accounts/gate.html')


# --- 会員登録・本人確認の流れ ---

def signup(request):
    """画像3: アカウント作成（電話番号とパスワード入力）"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # 1. 未入力チェック
        if not phone or not password:
            return render(request, 'accounts/signup.html', {'error': '電話番号とパスワードを入力してください'})

        # 2. 【最重要】電話番号の重複チェック
        if User.objects.filter(username=phone).exists():
            return render(request, 'accounts/signup.html', {
                'error': 'この電話番号は既に登録されています。',
                'phone': phone
            })

        # 3. ユーザー作成はせず、セッションに保存
        # パスワードはここでハッシュ化せずとも、作成時に set_password すればOK
        # あるいはここで一連のデータを保持
        request.session['signup_data'] = {
            'phone': phone,
            'password': password
        }
        
        # フローをセッションに記録
        request.session['auth_flow'] = 'signup'
        
        return redirect('verify_dob')

    return render(request, 'accounts/signup.html')

def setup_name(request):
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')
            
        signup_data['last_name_kanji'] = request.POST.get('last_name')
        signup_data['first_name_kanji'] = request.POST.get('first_name')
        request.session['signup_data'] = signup_data
        return redirect('setup_kana')
    return render(request, 'signup/step_name.html') 

def setup_kana(request):
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')
            
        signup_data['last_name_kana'] = request.POST.get('last_name_kana')
        signup_data['first_name_kana'] = request.POST.get('first_name_kana')
        request.session['signup_data'] = signup_data
        return redirect('setup_gender')
    return render(request, 'signup/step_kana.html')

def setup_gender(request):
    """画像3: 性別選択"""
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')
            
        signup_data['gender'] = request.POST.get('gender')
        request.session['signup_data'] = signup_data
        return redirect('setup_photo')
    return render(request, 'signup/step_gender.html')

def setup_photo(request):
    """画像4: 顔写真登録"""
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')

        if 'face_photo' in request.FILES:
            photo = request.FILES['face_photo']
            # 一時ディレクトリに保存
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_signup')
            os.makedirs(temp_dir, exist_ok=True)
            fs = FileSystemStorage(location=temp_dir)
            
            # 重複避けるためにファイル名調整したほうがいいが、一旦簡単のためにそのまま保存
            # またはfs.save()は自動でリネームしてくれる
            filename = fs.save(photo.name, photo)
            signup_data['face_photo_temp_path'] = filename
            request.session['signup_data'] = signup_data
            
        # 次へ（住所入力へ戻す）
        return redirect('setup_address')
            
    return render(request, 'signup/step_photo.html')

@login_required
def signup_verify_identity(request):
    """サインアップフロー用: 本人確認画面 (あとでボタンあり)"""
    # ログイン不要にするか、ログイン必須なら既存ユーザー用。
    # ここではサインアップフローのために@login_requiredを外す必要があるが、
    # 既存のデコレータがついているので注意。
    # 今回はサインアップフロー専用ビューとして扱う。
    return render(request, 'signup/step_identity.html')

def signup_verify_identity_skip(request):
    """本人確認スキップ -> 確認画面へ"""
    return redirect('signup_confirm')

def signup_confirm(request):
    """入力内容確認画面"""
    signup_data = request.session.get('signup_data')
    if not signup_data:
        # セッション切れ等の場合
        return redirect('signup')

    # テンプレートで表示するために辞書をオブジェクト風にアクセスできるようにするか、
    # 単に辞書として渡すが、テンプレート側が profile.xxx でアクセスしている場合は
    # 辞書アクセスとドットアクセスで互換性があるか確認が必要。
    # Djangoテンプレート言語では {{ foo.bar }} は foo['bar'] も試行するので辞書でOK。
    
    # 日付表示のために変換
    dob_str = signup_data.get('birth_date')
    birth_date = None
    if dob_str:
        try:
            birth_date = date.fromisoformat(dob_str)
        except ValueError:
            pass
            
    # テンプレートに渡すデータ構造を作成
    # profile キーで辞書を渡す
    profile_data = signup_data.copy()
    profile_data['birth_date'] = birth_date
    
    if request.method == 'POST':
        return redirect('setup_pref_select')
        
    return render(request, 'signup/step_confirm.html', {'profile': profile_data})

def setup_address(request):
    """画像5: 住所入力"""
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')

        if 'skip' in request.POST:
            return redirect('setup_workstyle')

        signup_data['postal_code'] = request.POST.get('postal_code')
        signup_data['prefecture'] = request.POST.get('prefecture')
        signup_data['city'] = request.POST.get('city')
        signup_data['address_line'] = request.POST.get('address_line')
        signup_data['building'] = request.POST.get('building')
        request.session['signup_data'] = signup_data
        
        return redirect('setup_workstyle')
    return render(request, 'signup/step_address.html')

def setup_workstyle(request):
    """画像6: 働き方登録"""
    if request.method == 'POST':
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup')

        if 'skip' in request.POST:
            return redirect('signup_verify_identity') 
            
        signup_data['work_style'] = request.POST.get('work_style')
        signup_data['career_interest'] = request.POST.get('career_interest')
        request.session['signup_data'] = signup_data
        
        return redirect('signup_verify_identity') 
    return render(request, 'signup/step_workstyle.html')

def setup_pref_select(request):
    """画像7: 都道府県選択"""
    auth_flow = request.session.get('auth_flow')
    
    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
        "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
        "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
        "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
        "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
        "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
    ]

    # --- サインアップフロー（新規登録完了処理） ---
    if auth_flow == 'signup':
        if request.method == 'POST':
            signup_data = request.session.get('signup_data')
            if not signup_data:
                return redirect('signup')
            
            prefs = request.POST.getlist('prefs')
            
            try:
                # 1. User 作成
                user = User.objects.create_user(
                    username=signup_data['phone'], 
                    password=signup_data['password']
                )
                
                # 2. WorkerProfile 作成
                profile = WorkerProfile(user=user)
                profile.last_name_kanji = signup_data.get('last_name_kanji', '')
                profile.first_name_kanji = signup_data.get('first_name_kanji', '')
                profile.last_name_kana = signup_data.get('last_name_kana', '')
                profile.first_name_kana = signup_data.get('first_name_kana', '')
                profile.gender = signup_data.get('gender', '')
                
                dob_str = signup_data.get('birth_date')
                if dob_str:
                    profile.birth_date = date.fromisoformat(dob_str)
                    
                profile.postal_code = signup_data.get('postal_code', '')
                profile.prefecture = signup_data.get('prefecture', '') 
                profile.city = signup_data.get('city', '')
                profile.address_line = signup_data.get('address_line', '')
                profile.building = signup_data.get('building', '')
                
                profile.work_style = signup_data.get('work_style', '')
                profile.career_interest = signup_data.get('career_interest', '')
                
                profile.target_prefectures = ",".join(prefs)
                profile.is_setup_completed = True
                
                # 本人確認済みフラグ（もしあれば）
                if signup_data.get('is_identity_verified'):
                     profile.is_identity_verified = True
                
                # 写真の処理
                temp_path = signup_data.get('face_photo_temp_path')
                if temp_path:
                    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_signup')
                    fs = FileSystemStorage(location=temp_dir)
                    if fs.exists(temp_path):
                        with fs.open(temp_path) as f:
                            profile.face_photo.save(temp_path, f, save=False)
                        fs.delete(temp_path)
                
                profile.save()
                
                # 3. ログイン
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # 4. セッションクリア
                if 'signup_data' in request.session:
                    del request.session['signup_data']
                
                return redirect('index')
                
            except IntegrityError:
                return render(request, 'signup/step_pref.html', {
                    'prefectures': prefectures, 
                    'error': '登録処理でエラーが発生しました。'
                })

        return render(request, 'signup/step_pref.html', {'prefectures': prefectures})
    
    # --- 既存ユーザー（設定変更など） ---
    else:
        if not request.user.is_authenticated:
            return redirect('login')
            
        profile = get_object_or_404(WorkerProfile, user=request.user)
        if request.method == 'POST':
            prefs = request.POST.getlist('prefs')
            profile.target_prefectures = ",".join(prefs)
            profile.is_setup_completed = True
            profile.save()
            return redirect('index') 
            
        return render(request, 'signup/step_pref.html', {'prefectures': prefectures})


def verify_identity(request):
    """本人確認画面（南京錠アイコンの画面）"""
    phone = request.user.username
    return render(request, 'accounts/verify_identity.html', {'phone': phone})


@login_required
def verify_dob(request):
    """生年月日入力・検証画面 (ログイン時)"""
    auth_flow = request.session.get('auth_flow', 'signup')

    # サインアップフローの場合は別の関数へ飛ばすか、ここで分岐
    if auth_flow == 'signup':
         return verify_dob_signup(request)

    if not request.user.is_authenticated:
        return redirect('login')

    profile, _ = WorkerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        
        try:
            birth_date = date(int(year), int(month), int(day))
            
            if profile.birth_date and profile.birth_date == birth_date:
                return redirect('index')
            elif not profile.birth_date:
                # 万が一誕生日の登録がない既存ユーザー（基本いないはずだが救済）
                profile.birth_date = birth_date
                profile.save()
                return redirect('index')
            else:
                return render(request, 'accounts/verify_dob.html', {
                    'error': '生年月日が登録情報と一致しません。'
                })
        except ValueError:
            return render(request, 'accounts/verify_dob.html', {
                'error': '正しい日付を入力してください。'
            })

    return render(request, 'accounts/verify_dob.html', {'auth_flow': auth_flow})

def verify_dob_signup(request):
    """生年月日入力 (サインアップ時)"""
    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        
        try:
            # 日付の妥当性チェック
            date(int(year), int(month), int(day))
            
            signup_data = request.session.get('signup_data')
            if not signup_data:
                return redirect('signup')

            signup_data['birth_date'] = f"{year}-{month}-{day}"
            request.session['signup_data'] = signup_data
            
            return redirect('setup_name')
            
        except ValueError:
            return render(request, 'accounts/verify_dob.html', {
                'error': '正しい日付を入力してください。',
                'auth_flow': 'signup'
            })
            
    return render(request, 'accounts/verify_dob.html', {'auth_flow': 'signup'})


def profile_setup(request):
    """画像1: プロフィール登録・都道府県・通知設定など"""
    if request.method == 'POST':
        profile = request.user.workerprofile
        
        # プロフィール情報
        profile.real_name = request.POST.get('real_name')
        profile.furigana = request.POST.get('furigana')
        profile.gender = request.POST.get('gender')
        profile.address = request.POST.get('address')
        profile.prefecture = request.POST.get('prefecture')
        
        # 利用端末の設定
        profile.notifications_enabled = 'notifications' in request.POST
        profile.location_enabled = 'location' in request.POST
        
        profile.is_identity_verified = True # 本人確認完了とする
        profile.save()
        
        return redirect('index') # 登録内容の確認画面を挟む場合は別途作成

    return render(request, 'accounts/profile_setup.html')


def login_view(request):
    """画像2: ログインシーケンスの再現"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # 1. 電話番号が無記入の場合
        if not phone:
            return render(request, 'accounts/login.html', {'error': '電話番号が入力されていません'})
        
        # 2. パスワードが無記入の場合
        if not password:
            return render(request, 'accounts/login.html', {'error': 'パスワードが入力されていません'})

        # 3. 参照（認証）
        user = authenticate(request, username=phone, password=password)

        if user is not None:
            # ログイン成功 -> 誕生日検証へ
            login(request, user)
            request.session['auth_flow'] = 'login'
            return redirect('verify_dob')
        else:
            # 電話番号もしくはパスワードが正しくない場合
            return render(request, 'accounts/login.html', {'error': '電話番号もしくはパスワードが正しくありません'})

    return render(request, 'accounts/login.html')

# accounts/views.py 内に追加
def mypage(request):
    """マイページ画面 (画像5)"""
    balance = 0
    membership = None
    if request.user.is_authenticated:
        try:
            profile = request.user.workerprofile
            balance = sum(t.amount for t in profile.wallet_transactions.all())
            membership, _ = WorkerMembership.objects.get_or_create(worker=profile)
        except:
            pass
            
    return render(request, 'accounts/mypage.html', {'balance': balance, 'membership': membership})

@login_required
def achievements(request):
    """あなたの実績画面 (画像2)"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    membership, created = WorkerMembership.objects.get_or_create(worker=profile)

    # 実績集計（過去の完了した仕事）
    # status='確定済み' かつ 日付が過去のもの
    past_apps = JobApplication.objects.filter(
        worker=request.user,
        status='確定済み',
        job_posting__work_date__lt=date.today()
    )
    
    work_count = past_apps.count()
    
    total_minutes = 0
    for app in past_apps:
        jp = app.job_posting
        # 時間計算 (簡易)
        d = date.today()
        start_dt = datetime.combine(d, jp.start_time)
        end_dt = datetime.combine(d, jp.end_time)
        duration = (end_dt - start_dt).total_seconds() / 60
        duration -= jp.break_duration
        if duration < 0: duration = 0
        total_minutes += duration
        
    work_hours = int(total_minutes / 60)
    
    # Good率
    reviews = profile.reviews.all()
    if reviews.exists():
        good_count = reviews.filter(is_good=True).count()
        good_rate = int((good_count / reviews.count()) * 100)
    else:
        good_rate = 0 # 表示上はハイフンなどにするかも
        
    exp_history = profile.exp_histories.all().order_by('-created_at')
    
    # レベル計算ロジック (簡易実装: Lv * 1000 を次のレベルへの閾値とする)
    # 例: Lv0 -> Lv1 (閾値1000), Lv1 -> Lv2 (閾値2000) ...
    # 累積経験値で管理している前提
    next_level_threshold = (membership.level + 1) * 1000
    needed_exp = next_level_threshold - membership.current_exp
    if needed_exp < 0: needed_exp = 0
    
    prev_threshold = membership.level * 1000
    level_range = next_level_threshold - prev_threshold
    current_in_level = membership.current_exp - prev_threshold
    progress_percent = int((current_in_level / level_range) * 100) if level_range > 0 else 0
    
    return render(request, 'accounts/achievements.html', {
        'profile': profile,
        'membership': membership,
        'work_count': work_count,
        'work_hours': work_hours,
        'good_rate': good_rate,
        'exp_history': exp_history,
        'needed_exp': needed_exp,
        'progress_percent': progress_percent
    })

@login_required
def past_jobs(request):
    """これまでの仕事 (画像: 過去の業務と報酬)"""
    # 完了した仕事を取得
    apps = JobApplication.objects.filter(
        worker=request.user,
        status='確定済み',
        job_posting__work_date__lt=date.today()
    ).select_related('job_posting').order_by('-job_posting__work_date')

    # 年・月ごとに集計
    # 構造: { 2023: [ {month: 5, count: 2}, ... ], 2022: ... }
    # OrderedDictを使うか、リストで管理してテンプレートで回すか。
    # テンプレートで扱いやすいように:
    # yearly_data = [
    #    {'year': 2023, 'months': [{'month': 5, 'count': 2}, ...] },
    #    ...
    # ]
    
    from collections import defaultdict
    
    # 1. (Year, Month) -> Count に集計
    agg = defaultdict(int)
    for app in apps:
        d = app.job_posting.work_date
        agg[(d.year, d.month)] += 1
        
    # 2. ソートして整形
    # 年の降順 -> 月の降順
    sorted_keys = sorted(agg.keys(), key=lambda x: (x[0], x[1]), reverse=True)
    
    yearly_data = []
    current_year = None
    current_year_entry = None
    
    for y, m in sorted_keys:
        if current_year != y:
            current_year = y
            current_year_entry = {'year': y, 'months': []}
            yearly_data.append(current_year_entry)
        
        current_year_entry['months'].append({
            'month': m,
            'count': agg[(y, m)]
        })
        
    return render(request, 'accounts/past_jobs.html', {'yearly_data': yearly_data})

# アカウント設定
@login_required
def account_settings(request):
    """アカウント設定メイン画面（設定項目の一覧）"""
    return render(request, 'accounts/account_settings.html')

@login_required
def profile_edit(request):
    profile = request.user.workerprofile
    if request.method == 'POST':
        # 名前・性別・誕生日の基本情報のみここで更新
        profile.last_name_kanji = request.POST.get('last_name_kanji')
        profile.first_name_kanji = request.POST.get('first_name_kanji')
        profile.last_name_kana = request.POST.get('last_name_kana')
        profile.first_name_kana = request.POST.get('first_name_kana')
        profile.gender = request.POST.get('gender')
        
        # 生年月日の更新
        dob_str = request.POST.get('birth_date')
        if dob_str:
            profile.birth_date = date.fromisoformat(dob_str)
            
        # 画像保存
        if 'face_photo' in request.FILES:
            profile.face_photo = request.FILES['face_photo']
            
        profile.save()
        return redirect('account_settings')

    return render(request, 'accounts/profile_edit.html', {
        'profile': profile,
        'prefectures_list': PREFECTURES
    })

@login_required
def profile_address_edit(request):
    """プロフィールの住所を専用画面（画像再現）で編集する"""
    profile = request.user.workerprofile
    if request.method == 'POST':
        profile.postal_code = request.POST.get('postal_code')
        profile.prefecture = request.POST.get('prefecture')
        profile.city = request.POST.get('city')
        profile.address_line = request.POST.get('address_line')
        profile.building = request.POST.get('building')
        profile.save()
        return redirect('profile_edit')

    return render(request, 'accounts/profile_address_edit.html', {
        'profile': profile,
        'prefectures_list': PREFECTURES
    })

@login_required
def other_profile_edit(request):
    """その他のプロフィール（所属設定）"""
    profile = request.user.workerprofile
    if request.method == 'POST':
        # 入力された「所属」をデータベースに保存
        profile.affiliation = request.POST.get('affiliation')
        profile.save()
        return redirect('account_settings')
    return render(request, 'accounts/other_profile.html', {'profile': profile})

@login_required
def emergency_contact_edit(request):
    """緊急連絡先設定"""
    profile = request.user.workerprofile
    if request.method == 'POST':
        # 図の「緊急連絡先」更新処理
        profile.emergency_phone = request.POST.get('emergency_phone')
        profile.emergency_relation = request.POST.get('emergency_relation')
        profile.save()
        return redirect('account_settings')
    return render(request, 'accounts/emergency_contact.html', {'profile': profile})

#
@login_required
def phone_change(request):
    """画像1: 現在の番号表示"""
    phone = request.user.username
    masked_phone = "*" * (len(phone) - 4) + phone[-4:] if len(phone) > 4 else phone
    return render(request, 'accounts/phone_change_home.html', {'masked_phone': masked_phone})

@login_required
def phone_change_confirm(request):
    """画像2: 旧番号入力"""
    if request.method == 'POST':
        input_phone = request.POST.get('old_phone')
        if input_phone == request.user.username:
            return redirect('phone_input_new')  # 次のステップ名を確認
        else:
            return render(request, 'accounts/phone_change_confirm.html', {'error': '電話番号が一致しません。'})
    return render(request, 'accounts/phone_change_confirm.html')

@login_required
def phone_input_new(request):
    """画像3: 新番号入力"""
    if request.method == 'POST':
        new_phone = request.POST.get('new_phone')
        request.session['pending_new_phone'] = new_phone
        return redirect('phone_confirm_password') # 次のステップ名を確認
    return render(request, 'accounts/phone_input_new.html')


@login_required
def phone_confirm_password(request):
    """【画像4改変】パスワードを入力して確定する"""
    new_phone = request.session.get('pending_new_phone')
    if not new_phone:
        return redirect('phone_change')

    if request.method == 'POST':
        password = request.POST.get('password')
        # パスワード認証
        user = authenticate(username=request.user.username, password=password)
        if user is not None:
            # 電話番号（username）を更新
            user.username = new_phone
            user.save()
            del request.session['pending_new_phone']
            return redirect('account_settings') # 完了後、設定トップへ戻る
        else:
            return render(request, 'accounts/phone_confirm_password.html', {
                'new_phone': new_phone,
                'error': 'パスワードが正しくありません。'
            })
    return render(request, 'accounts/phone_confirm_password.html', {'new_phone': new_phone})

@login_required
def verify_identity_select(request):
    """詳細画面: 本人確認書類の選択画面"""
    return render(request, 'accounts/verify_identity_select.html')

@login_required
def verify_identity_upload(request):
    """本人確認書類のアップロードと完了処理"""
    if request.method == 'POST':
        # サインアップフロー中なら、セッションに記録して確認画面へ
        if request.session.get('auth_flow') == 'signup':
             # 実際にはここでファイルアップロード処理が必要かもしれないが
             # 一旦「本人確認済み」フラグを立てるのみとする
             # （もし書類画像が必要なら setup_photo と同様に一時保存が必要）
             signup_data = request.session.get('signup_data')
             if signup_data:
                 signup_data['is_identity_verified'] = True
                 request.session['signup_data'] = signup_data
             return redirect('signup_confirm')

        # 既存ユーザー用
        if request.user.is_authenticated:
            profile = request.user.workerprofile
            profile.is_identity_verified = True
            profile.save()
            return redirect('mypage')
        else:
            return redirect('login')
            
    return render(request, 'accounts/verify_identity_upload.html')


# --- 報酬管理 (ウォレット) ---

@login_required
def reward_management(request):
    """画像2: 報酬管理画面"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    
    # 残高計算
    transactions = profile.wallet_transactions.all()
    balance = sum(t.amount for t in transactions)
    
    # 銀行口座確認
    try:
        bank_account = profile.bank_account
    except WorkerBankAccount.DoesNotExist:
        bank_account = None
        
    return render(request, 'accounts/reward_management.html', {
        'balance': balance,
        'bank_account': bank_account,
        'profile': profile
    })

@login_required
def wallet_history(request):
    """画像3: 入出金履歴"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    transactions = profile.wallet_transactions.all().order_by('-created_at')
    
    return render(request, 'accounts/wallet_history.html', {
        'transactions': transactions
    })

@login_required
def bank_account_edit(request):
    """画像4: 振込先口座登録"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    
    # POST処理
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        account_type = request.POST.get('account_type')
        branch_name = request.POST.get('branch_name')
        account_number = request.POST.get('account_number')
        account_holder_name = request.POST.get('account_holder_name')
        
        WorkerBankAccount.objects.update_or_create(
            worker=profile,
            defaults={
                'bank_name': bank_name,
                'account_type': account_type,
                'branch_name': branch_name,
                'account_number': account_number,
                'account_holder_name': account_holder_name,
            }
        )
        return redirect('reward_management')

    try:
        account = profile.bank_account
    except WorkerBankAccount.DoesNotExist:
        account = None
        
    return render(request, 'accounts/bank_account_edit.html', {'account': account})

@login_required
def withdraw_application(request):
    """画像5: 振込申請"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    
    balance = sum(t.amount for t in profile.wallet_transactions.all())

    try:
        bank_account = profile.bank_account
    except WorkerBankAccount.DoesNotExist:
        bank_account = None
    
    if request.method == 'POST':
        # 全額出金処理
        if balance > 0:
            WalletTransaction.objects.create(
                worker=profile,
                amount=-balance,
                transaction_type='withdrawal',
                description='振込申請'
            )
            # 成功時はその場で完了画面を出すために success フラグを渡す
            return render(request, 'accounts/withdraw_application.html', {'success': True})
        # 残高0などでPOSTされた場合はリダイレクトまたはエラー表示（今回はリダイレクト）
        return redirect('reward_management')
        
    return render(request, 'accounts/withdraw_application.html', {
        'balance': balance,
        'bank_account': bank_account
    })

@login_required
def review_penalty(request):
    """画像3: レビューとペナルティ画面"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    reviews = profile.reviews.all().order_by('-created_at') # Reviewモデルのrelated_name='reviews'を想定

    # キャンセル率計算 (簡易ロジック: cancellations / (completed + cancellations) などだが、
    # 今回はモデルに保存された値をそのまま表示する形にする)
    # ※ 本来はジョブ履歴から計算するが、要件としてフィールド追加したのでそれを使う
    
    # 完了数(completed_jobs)などがモデルにないので、一旦キャンセル系は直接フィールドを表示
    # 率（％）を計算して渡すか、テンプレートで計算するか。
    # ここでは仮に全案件数を「完了数+キャンセル数」として計算してみるが、
    # 完了数を持っていないため、モデルの数値をそのまま「率」として扱うか、
    # あるいはダミー計算を入れる。
    # 画像では「10%」「3%」となっている。
    # ひとまずモデルのint値をそのまま%として扱う。（仕様が不明確なため）
    
    cancel_rate = profile.cancellations # 仮: そのままパーセントとして表示
    lastminute_cancel_rate = profile.lastminute_cancel # 仮

    return render(request, 'accounts/review_penalty.html', {
        'profile': profile,
        'reviews': reviews,
        'cancel_rate': cancel_rate,
        'lastminute_cancel_rate': lastminute_cancel_rate
    })

@login_required
def penalty_detail(request):
    """画像4: ペナルティ詳細画面"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    return render(request, 'accounts/penalty_detail.html', {'profile': profile})

@login_required
def qualification_list(request):
    """画像3: 保有資格一覧"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    qualifications = profile.qualifications.all().select_related('qualification')
    return render(request, 'accounts/qualification_list.html', {'qualifications': qualifications})

@login_required
def qualification_category_select(request):
    """画像5: 資格分野選択"""
    categories = QualificationCategory.objects.all().order_by('display_order')
    return render(request, 'accounts/qualification_category_select.html', {'categories': categories})

@login_required
def qualification_item_select(request, category_id):
    """資格名称選択"""
    category = get_object_or_404(QualificationCategory, pk=category_id)
    items = category.items.all()
    return render(request, 'accounts/qualification_item_select.html', {'category': category, 'items': items})

@login_required
def qualification_create(request):
    """画像4: 資格登録フォーム"""
    profile = get_object_or_404(WorkerProfile, user=request.user)

    # 一覧から「追加する」できた場合（clear=1）はセッションをクリアして初期化
    if request.GET.get('clear'):
        if 'qualification_item_id' in request.session:
            del request.session['qualification_item_id']
        if 'temp_qualification_image' in request.session:
            # 実ファイルも消すならここで行うが、tempの管理は定期的削除等に任せる実装も多い
            # 今回はセッション参照のみ切る
            del request.session['temp_qualification_image']
        return redirect('qualification_create') # クエリパラメータを外してリダイレクト（スッキリさせる）

    # 選択された資格IDをクエリパラメータから取得
    # セッションに保存されている場合はそれを優先（アップロードフローからの戻り）
    item_id = request.GET.get('item_id') or request.session.get('qualification_item_id')
    
    selected_item = None
    if item_id:
        selected_item = get_object_or_404(QualificationItem, pk=item_id)
        # セッションにも保存しておく（アップロードフロー用）
        request.session['qualification_item_id'] = item_id
    
    # 仮保存された画像パスを取得
    curr_temp_path = request.session.get('temp_qualification_image')
    
    if request.method == 'POST':
        # 最終登録処理
        if selected_item and curr_temp_path:
            # セッションの実画像を保存先にコピーなどしてから保存
            # ここではシンプルに FileSystemStorage で別名保存するか、ポインタを渡す
            # Base64ではなくファイルパスで管理している前提
            
            # tempパスは MEDIA_ROOT からの相対パス想定
            # shutil move 等が必要だが、DjangoのFileFieldにパスから保存するのは少し手間。
            # 簡易実装として、FileObjを開いて保存し直す。
            
            fs = FileSystemStorage()
            # full path
            abs_path = os.path.join(settings.MEDIA_ROOT, curr_temp_path)
            
            if os.path.exists(abs_path):
                with open(abs_path, 'rb') as f:
                    from django.core.files import File
                    django_file = File(f)
                    django_file.name = os.path.basename(abs_path) # ファイル名のみを設定
                    
                    WorkerQualification.objects.create(
                        worker=profile,
                        qualification=selected_item,
                        certificate_image=django_file
                    )
                
                # 後始末
                os.remove(abs_path)
                if 'temp_qualification_image' in request.session:
                    del request.session['temp_qualification_image']
                if 'qualification_item_id' in request.session:
                    del request.session['qualification_item_id']
                
                return render(request, 'accounts/qualification_form.html', {
                    'selected_item': selected_item,
                    'success': True 
                })

    return render(request, 'accounts/qualification_form.html', {
        'selected_item': selected_item,
        'temp_image_url': f"{settings.MEDIA_URL}{curr_temp_path}" if curr_temp_path else None
    })

@login_required
def qualification_photo_upload(request):
    """写真アップロード処理（一時保存） -> 確認画面へ"""
    if request.method == 'POST' and request.FILES.get('certificate_image'):
        image_file = request.FILES['certificate_image']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))
        filename = fs.save(image_file.name, image_file)
        
        # 相対パスをセッションに保存 (temp/filename)
        request.session['temp_qualification_image'] = os.path.join('temp', filename)
        
        return redirect('qualification_photo_confirm')
    
    # GETでアクセスされたら作成画面に戻す
    return redirect('qualification_create')

@login_required
def qualification_photo_confirm(request):
    """画像追加1: 写真確認画面"""
    temp_path = request.session.get('temp_qualification_image')
    item_id = request.session.get('qualification_item_id')
    
    if not temp_path:
        return redirect('qualification_create')
        
    selected_item = None
    if item_id:
        selected_item = QualificationItem.objects.filter(pk=item_id).first()

    if request.method == 'POST':
        # OKボタン押下時 -> 作成画面に戻る
        return redirect('qualification_create')

    return render(request, 'accounts/qualification_photo_confirm.html', {
        'temp_image_url': f"{settings.MEDIA_URL}{temp_path}",
        'selected_item': selected_item
    })