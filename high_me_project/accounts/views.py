from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import WorkerProfile
from django.db import IntegrityError
from django.contrib.auth import authenticate, login

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
        # すでに登録されている場合は、エラーメッセージを出して同じ画面に戻す
        if User.objects.filter(username=phone).exists():
            return render(request, 'accounts/signup.html', {
                'error': 'この電話番号は既に登録されています。',
                'phone': phone  # 入力していた番号を戻してあげる
            })

        try:
            # 3. ユーザー作成
            user = User.objects.create_user(username=phone, password=password)
            login(request, user)
            return redirect('verify_identity')
        except IntegrityError:
            # 万が一、同時送信などで重複が発生した場合の保険
            return render(request, 'accounts/signup.html', {'error': '登録エラーが発生しました。もう一度お試しください。'})

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
            # ログイン成功 -> さがす画面へ
            login(request, user)
            return redirect('index')
        else:
            # 電話番号もしくはパスワードが正しくない場合
            return render(request, 'accounts/login.html', {'error': '電話番号もしくはパスワードが正しくありません'})

    return render(request, 'accounts/login.html')

# accounts/views.py 内に追加
def mypage(request):
    """マイページ画面 (画像5)"""
    return render(request, 'accounts/mypage.html')

# アカウント設定
@login_required
def account_settings(request):
    """アカウント設定メイン画面（設定項目の一覧）"""
    return render(request, 'accounts/account_settings.html')

@login_required
def profile_edit(request):
    profile = request.user.workerprofile
    if request.method == 'POST':
        # 名前の更新
        request.user.last_name = request.POST.get('last_name')
        request.user.first_name = request.POST.get('first_name')
        request.user.save()

        # プロフィール情報の更新
        profile.last_name_kana = request.POST.get('last_kana')
        profile.first_name_kana = request.POST.get('first_kana')
        profile.gender = request.POST.get('gender')
        profile.birth_date = request.POST.get('birth_date')

        # ★ 画像の保存処理を追加
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        
        profile.save()
        return redirect('account_settings')
    
    return render(request, 'accounts/profile_edit.html', {'profile': profile})

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