from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import WorkerProfile
from django.db import IntegrityError
from django.contrib.auth import authenticate, login
from datetime import date
from jobs.views import PREFECTURES

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
            
            # フローをセッションに記録
            request.session['auth_flow'] = 'signup'
            
            return redirect('verify_dob')
        except IntegrityError:
            # 万が一、同時送信などで重複が発生した場合の保険
            return render(request, 'accounts/signup.html', {'error': '登録エラーが発生しました。もう一度お試しください。'})

    return render(request, 'accounts/signup.html')

@login_required
def setup_name(request):
    if request.method == 'POST':
        profile, _ = WorkerProfile.objects.get_or_create(user=request.user)
        profile.last_name_kanji = request.POST.get('last_name')
        profile.first_name_kanji = request.POST.get('first_name')
        profile.save()
        return redirect('setup_kana')
    # パスを 'signup/...' に修正
    return render(request, 'signup/step_name.html') 

@login_required
def setup_kana(request):
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        profile.last_name_kana = request.POST.get('last_name_kana')
        profile.first_name_kana = request.POST.get('first_name_kana')
        profile.save()
        return redirect('setup_gender')
    return render(request, 'signup/step_kana.html')

@login_required
def setup_gender(request):
    """画像3: 性別選択"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        profile.gender = request.POST.get('gender')
        profile.save()
        return redirect('setup_photo')
    return render(request, 'signup/step_gender.html')

@login_required
def setup_photo(request):
    """画像4: 顔写真登録"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        if 'skip' in request.POST: # 「あとで」ボタン
            return redirect('setup_address')
        if 'face_photo' in request.FILES:
            profile.face_photo = request.FILES['face_photo']
            profile.save()
            return redirect('setup_address')
    return render(request, 'signup/step_photo.html')

@login_required
def setup_address(request):
    """画像5: 住所入力"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        if 'skip' in request.POST:
            return redirect('setup_workstyle')
        profile.postal_code = request.POST.get('postal_code')
        profile.prefecture = request.POST.get('prefecture')
        profile.city = request.POST.get('city')
        profile.address_line = request.POST.get('address_line')
        profile.building = request.POST.get('building')
        profile.save()
        return redirect('setup_workstyle')
    return render(request, 'signup/step_address.html')

@login_required
def setup_workstyle(request):
    """画像6: 働き方登録"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        if 'skip' in request.POST:
            return redirect('setup_pref_select')
        profile.work_style = request.POST.get('work_style')
        profile.career_interest = request.POST.get('career_interest')
        profile.save()
        return redirect('setup_pref_select')
    return render(request, 'signup/step_workstyle.html')

@login_required
def setup_pref_select(request):
    """画像7: 都道府県選択"""
    profile = get_object_or_404(WorkerProfile, user=request.user)
    if request.method == 'POST':
        # チェックボックスのリストを取得
        prefs = request.POST.getlist('prefs')
        profile.target_prefectures = ",".join(prefs)
        profile.is_setup_completed = True
        profile.save()
        return redirect('index') # 最後にホームへ
        
    prefectures = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都"] # 以下略
    return render(request, 'signup/step_pref.html', {'prefectures': prefectures})


def verify_identity(request):
    """本人確認画面（南京錠アイコンの画面）"""
    phone = request.user.username
    return render(request, 'accounts/verify_identity.html', {'phone': phone})


@login_required
def verify_dob(request):
    """生年月日入力・検証画面"""
    auth_flow = request.session.get('auth_flow', 'signup')
    profile, _ = WorkerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        
        try:
            birth_date = date(int(year), int(month), int(day))
            
            if auth_flow == 'login':
                # ログイン時の検証ロジック
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
            else:
                # 新規登録時の保存ロジック
                profile.birth_date = birth_date
                profile.save()
                return redirect('setup_name')
            
        except ValueError:
            return render(request, 'accounts/verify_dob.html', {
                'error': '正しい日付を入力してください。'
            })

    return render(request, 'accounts/verify_dob.html', {'auth_flow': auth_flow})


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
        # プロフィールを本人確認済みに更新
        profile = request.user.workerprofile
        profile.is_identity_verified = True
        profile.save()
        return redirect('mypage')
    return render(request, 'accounts/verify_identity_upload.html')