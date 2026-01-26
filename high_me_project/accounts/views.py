from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import WorkerProfile, WorkerBankAccount, WalletTransaction
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
    if request.user.is_authenticated:
        try:
            profile = request.user.workerprofile
            balance = sum(t.amount for t in profile.wallet_transactions.all())
        except:
            pass
            
    return render(request, 'accounts/mypage.html', {'balance': balance})

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
    
    if request.method == 'POST':
        # 全額出金処理
        if balance > 0:
            WalletTransaction.objects.create(
                worker=profile,
                amount=-balance,
                transaction_type='withdrawal',
                description='振込申請'
            )
        return redirect('reward_management')
        
    return render(request, 'accounts/withdraw_application.html', {'balance': balance})