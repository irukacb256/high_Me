from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import BusinessProfile, Store, JobTemplate

# --- 登録フロー ---

def landing(request):
    """画像3: 事業者向けトップ（案内）画面"""
    return render(request, 'business/landing.html')

def signup(request):
    """ステップ1: メールアドレス入力 (画像4, 5)"""
    if request.method == 'POST':
        # セッションにメールを一時保存して次のステップへ
        request.session['signup_email'] = request.POST.get('email')
        return redirect('biz_account_register')
    return render(request, 'business/signup.html')

def account_register(request):
    """画像1: 管理者情報登録（User作成）"""
    email = request.session.get('signup_email', 'demo@example.com')
    if request.method == 'POST':
        # get('name属性の名前', '取れなかった時のデフォルト値')
        last_name = request.POST.get('last_name', "")
        first_name = request.POST.get('first_name', "")
        password = request.POST.get('password', "")
        
        # 値が空でないか念のためチェック
        if not last_name or not first_name or not password:
             return render(request, 'business/account_register.html', {
                 'email': email,
                 'error': '全ての項目を入力してください'
             })

        # DjangoのUser作成
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        login(request, user)
        return redirect('biz_business_register')
    return render(request, 'business/account_register.html', {'email': email})

@login_required
def business_register(request):
    """画像2・3: 事業者登録（BusinessProfile作成）"""
    if request.method == 'POST':
        BusinessProfile.objects.create(
            user=request.user,
            company_name=request.user.last_name + "株式会社", # 簡易生成
            business_type=request.POST.get('biz_type'),
        )
        return redirect('biz_verify')
    return render(request, 'business/business_register.html')

@login_required
def verify_docs(request):
    """画像6: 書類提出"""
    if request.method == 'POST':
        return redirect('biz_store_setup')
    return render(request, 'business/verify_docs.html')

@login_required
def store_setup(request):
    """画像7: 店舗登録（Store作成）"""
    if request.method == 'POST':
        try:
            biz_profile = BusinessProfile.objects.get(user=request.user)
            
            # フォームから値を取得
            store_name = request.POST.get('store_name')
            post_code = request.POST.get('post_code')
            
            # ★ バリデーション：店舗名が空ならエラーメッセージを出して再表示
            if not store_name:
                return render(request, 'business/store_setup.html', {'error': '店舗名を入力してください'})

            # 保存
            Store.objects.create(
                business=biz_profile,
                store_name=store_name,
                post_code=post_code,
                prefecture=request.POST.get('prefecture'),
                city=request.POST.get('city'),
                address_line=request.POST.get('address_line'),
                building=request.POST.get('building'),
            )
            
            # 登録完了後、一度ログアウトしてログイン画面へ（前回の指示通り）
            from django.contrib.auth import logout
            logout(request)
            return redirect('biz_login')
            
        except BusinessProfile.DoesNotExist:
            return redirect('biz_business_register')
            
    return render(request, 'business/store_setup.html')

def biz_login(request):
    """事業者用ログイン画面"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Django標準の認証（usernameにemailを入れている前提）
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('biz_dashboard')
        else:
            return render(request, 'business/login.html', {'error': 'メールアドレスまたはパスワードが正しくありません'})
    return render(request, 'business/login.html')


# --- 管理画面（ログイン中の情報を表示する） ---

def get_biz_context(request):
    """【共通ツール】ログインユーザーに紐づく店舗データを取得する"""
    try:
        biz_profile = BusinessProfile.objects.get(user=request.user)
        store = Store.objects.filter(business=biz_profile).first()
        return store
    except BusinessProfile.DoesNotExist:
        return None

@login_required
def dashboard(request):
    """ホーム画面"""
    # ログインユーザーに紐づく店舗を確実に取得
    biz_profile = BusinessProfile.objects.filter(user=request.user).first()
    store = Store.objects.filter(business=biz_profile).first() if biz_profile else None
    
    # templatesの取得
    templates = JobTemplate.objects.filter(store=store).order_by('-created_at') if store else []

    return render(request, 'business/dashboard.html', {
        'store': store,
        'templates': templates
    })

@login_required
def template_list(request):
    """ひな形一覧画面"""
    biz_profile = BusinessProfile.objects.filter(user=request.user).first()
    store = Store.objects.filter(business=biz_profile).first() if biz_profile else None
    
    # この店舗が作成したひな形を全件取得
    templates = JobTemplate.objects.filter(store=store).order_by('-created_at') if store else []
    
    return render(request, 'business/template_list.html', {
        'store': store,
        'templates': templates
    })

@login_required
def template_create(request):
    """ひな形作成フォーム"""
    store = get_biz_context(request)
    if request.method == 'POST' and store:
        JobTemplate.objects.create(
            store=store,
            title=request.POST.get('title'),
            industry=request.POST.get('industry'),
            occupation=request.POST.get('occupation'),
            work_content=request.POST.get('work_content'),
            address=request.POST.get('address'),
            access=request.POST.get('access'),
            contact_number=request.POST.get('contact_number'),
            auto_message=request.POST.get('auto_message'),
        )
        return redirect('biz_template_list')

    return render(request, 'business/template_form.html', {
        'store': store
    })