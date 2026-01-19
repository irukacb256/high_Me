from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import JobTemplate, JobPosting, Store, BusinessProfile

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
    """ログイン成功時のリダイレクト先をポータルへ"""
    if request.method == 'POST':
        # ... 認証ロジック ...
        return redirect('biz_portal') # ダッシュボードではなくポータルへ
    return render(request, 'business/login.html')

@login_required
def biz_portal(request):
    """画像1: 企業 / 店舗一覧（ログイン後の初期画面）"""
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    stores = Store.objects.filter(business=biz_profile)
    return render(request, 'business/portal.html', {
        'biz_profile': biz_profile,
        'stores': stores
    })


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
def dashboard(request, store_id):
    """店舗ホーム画面（カレンダー優先）"""
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    
    # この店舗の全求人を取得
    postings = JobPosting.objects.filter(template__store=store)

    return render(request, 'business/dashboard.html', {
        'store': store,
        'postings': postings,
    })

@login_required
def add_store(request):
    """新しい店舗を追加する（企業管理画面からの操作）"""
    if request.method == 'POST':
        biz_profile = BusinessProfile.objects.get(user=request.user)
        Store.objects.create(
            business=biz_profile,
            store_name=request.POST.get('store_name'),
            # ... 他の住所項目など
        )
        return redirect('biz_portal')
    return render(request, 'business/store_setup.html') # 以前作成したフォームを流用

@login_required
def template_list(request, store_id):
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    
    # ★ store=store で絞り込んでいるか確認
    templates = JobTemplate.objects.filter(store=store).order_by('-created_at')
    
    return render(request, 'business/template_list.html', {
        'store': store,
        'templates': templates
    })

@login_required
def template_create(request, store_id):
    # 1. 現在のユーザーに紐づく事業者プロフィールを取得
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    # 2. URLの store_id に基づいて、操作対象の店舗を特定
    store = get_object_or_404(Store, id=store_id, business=biz_profile)

    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            # 3. 保存時に「store=store」を必ず入れる！
            JobTemplate.objects.create(
                store=store,  # ★ここが抜けていると、誰のひな形か不明になりリストに出ません
                title=title,
                industry=request.POST.get('industry'),
                occupation=request.POST.get('occupation'),
                work_content=request.POST.get('work_content'),
                address=request.POST.get('address'),
                access=request.POST.get('access'),
                contact_number=request.POST.get('contact_number'),
                auto_message=request.POST.get('auto_message'),
            )
            # 4. 完了後のリダイレクト先にも store_id を含める
            return redirect('biz_template_list', store_id=store.id)

    return render(request, 'business/template_form.html', {'store': store})

@login_required
def template_detail(request, pk):
    """詳細画面"""
    store = get_biz_context(request)
    template = get_object_or_404(JobTemplate, pk=pk, store=store)
    return render(request, 'business/template_detail.html', {'template': template, 'store': store})

@login_required
def template_edit(request, pk):
    """編集画面 (template_form.html を再利用)"""
    store = get_biz_context(request)
    template = get_object_or_404(JobTemplate, pk=pk, store=store)

    if request.method == 'POST':
        template.title = request.POST.get('title')
        template.industry = request.POST.get('industry')
        template.occupation = request.POST.get('occupation')
        template.work_content = request.POST.get('work_content')
        template.precautions = request.POST.get('precautions')
        template.belongings = request.POST.get('belongings')
        template.requirements = request.POST.get('requirements')
        template.address = request.POST.get('address')
        template.access = request.POST.get('access')
        template.contact_number = request.POST.get('contact_number')
        template.auto_message = request.POST.get('auto_message')
        template.save()
        return redirect('biz_template_list')

    return render(request, 'business/template_form.html', {
        'template': template, 
        'store': store, 
        'is_edit': True
    })

# --- 求人作成フロー (画像3・4のシーケンス準拠) ---

@login_required
def job_create_from_template(request, template_pk):
    """画像1・2: ひな形を元に求人を作成(勤務日時設定)"""
    store = get_biz_context(request)
    template = get_object_or_404(JobTemplate, pk=template_pk, store=store)
    
    if request.method == 'POST':
        # シーケンス図: 必要情報を入力し「求人内容を確認」ボタンを押下
        # セッションに一時保存して確認画面へ
        request.session['pending_job'] = {
            'template_id': template.pk,
            'work_date': request.POST.get('work_date'),
            'start_time': request.POST.get('start_time'),
            'end_time': request.POST.get('end_time'),
            'title': request.POST.get('title'),
        }
        return redirect('biz_job_confirm')
    
    return render(request, 'business/job_create_form.html', {'template': template, 'store': store})

@login_required
def job_posting_list(request, store_id): # ★ store_id を引数に追加
    """店舗別の求人一覧画面"""
    # ログインユーザーの店舗であることを確認
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    
    # この店舗（store）に紐づく求人のみを取得
    postings = JobPosting.objects.filter(template__store=store).order_by('-work_date', '-start_time')
    
    return render(request, 'business/job_posting_list.html', {
        'store': store,      # サイドバーのURL生成に必要
        'postings': postings
    })

@login_required
def job_confirm(request):
    """求人公開の確定処理"""
    pending_data = request.session.get('pending_job')
    if not pending_data:
        return redirect('biz_template_list')
    
    if request.method == 'POST':
        if 'confirm_check' in request.POST:
            template = get_object_or_404(JobTemplate, pk=pending_data['template_id'])
            
            # 求人を作成
            JobPosting.objects.create(
                template=template,
                title=pending_data.get('title') or template.title,
                work_date=pending_data['work_date'],
                start_time=pending_data['start_time'],
                end_time=pending_data['end_time'],
                work_content=template.work_content,
                is_published=True
            )
            
            del request.session['pending_job']
            # ★ 修正：ダッシュボードではなく「求人一覧」へリダイレクト
            return redirect('biz_job_posting_list') 
        else:
            return render(request, 'business/job_confirm.html', {'error': 'チェックがされていません。', 'data': pending_data})

    return render(request, 'business/job_confirm.html', {'data': pending_data})