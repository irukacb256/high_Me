from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import WorkerProfile

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
    """
    画像3: アカウント作成（電話番号とパスワード入力）
    シーケンス図に基づいたバリデーションを実装
    """
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # 1. 未入力チェック
        if not phone:
            return render(request, 'accounts/signup.html', {'error': '電話番号を入力してください'})
        if not password:
            return render(request, 'accounts/signup.html', {'error': 'パスワードを入力してください'})

        # 2. 電話番号の重複チェック（電話番号をusernameとして扱う）
        if User.objects.filter(username=phone).exists():
            return render(request, 'accounts/signup.html', {'error': 'この電話番号は既に使用されています'})

        # 3. ユーザー作成と自動ログイン
        user = User.objects.create_user(username=phone, password=password)
        login(request, user)
        
        # 本人確認（南京錠の画面）へ遷移
        return redirect('verify_identity')

    return render(request, 'accounts/signup.html')


def verify_identity(request):
    """本人確認画面（南京錠アイコンの画面）"""
    phone = request.user.username
    return render(request, 'accounts/verify_identity.html', {'phone': phone})


def verify_dob(request):
    """本人確認画面（生年月日入力）"""
    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')

        if year and month and day:
            # プロフィールを作成または取得して生年月日を保存
            profile, created = WorkerProfile.objects.get_or_create(user=request.user)
            profile.birth_date = f"{year}-{month:0>2}-{day:0>2}" # YYYY-MM-DD形式
            profile.save()
            return redirect('profile_setup')

    return render(request, 'accounts/verify_dob.html')


def profile_setup(request):
    """
    ワーカー詳細登録画面
    氏名、フリガナ、性別、住所、働き方などを入力
    """
    if request.method == 'POST':
        # フォームからデータを取得
        furigana = request.POST.get('furigana')
        address = request.POST.get('address')
        working_style = request.POST.get('working_style')
        # ... 他の項目も同様に取得

        # プロフィールを更新
        profile = request.user.workerprofile
        profile.furigana = furigana
        profile.address = address
        profile.working_style = working_style
        # ... 他の項目も保存
        profile.save()

        # 全て完了したら「さがす（メイン画面）」へ
        return redirect('index')

    return render(request, 'accounts/profile_setup.html')


def login_view(request):
    """既存ユーザー用のログイン画面（Step 2以降で詳細実装）"""
    return render(request, 'accounts/login.html')