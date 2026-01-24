from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import WorkerProfile
from .models import JobApplication, JobTemplate, JobPosting, Store, BusinessProfile, QualificationMaster, JobTemplatePhoto

# --- 登録フロー ---

def landing(request):
    """画像3: 事業者向けトップ（案内）画面"""
    return render(request, 'business/landing.html')

def signup(request):
    """ステップ1: メールアドレス入力"""
    if request.method == 'POST':
        email = request.POST.get('email')
        consent = request.POST.get('consent') # 同意チェックボックス
        biz_type_radio = request.POST.get('p')

        errors = []
        # バリデーション
        if not email:
             errors.append('メールアドレスを入力してください')
        
        if not consent:
             errors.append('利用規約等への同意が必要です')
        
        if errors:
             return render(request, 'business/signup.html', {
                 'errors': errors,
                 'email': email,
                 'p_val': biz_type_radio
             })
        
        # セッションにメールを保存して次へ
        # 既存データの初期化も兼ねて辞書を作成
        request.session['biz_signup_data'] = {'email': email}
        return redirect('biz_account_register')

    return render(request, 'business/signup.html')

def account_register(request):
    """画像1: 管理者情報登録"""
    signup_data = request.session.get('biz_signup_data')
    if not signup_data:
        return redirect('biz_signup')
    
    email = signup_data.get('email')

    if request.method == 'POST':
        last_name = request.POST.get('last_name', "")
        first_name = request.POST.get('first_name', "")
        password = request.POST.get('password', "")
        # ここでメールアドレスの変更を受け付ける場合
        input_email = request.POST.get('email')
        
        if not last_name or not first_name or not password or not input_email:
             return render(request, 'business/account_register.html', {
                 'email': input_email or email,
                 'error': '全ての項目を入力してください'
             })

        # メールアドレスが変更されている可能性があるのでチェック
        if User.objects.filter(username=input_email).exists():
             return render(request, 'business/account_register.html', {
                 'email': input_email,
                 'error': 'このメールアドレスは既に登録されています。'
             })

        # セッションに保存
        signup_data['last_name'] = last_name
        signup_data['first_name'] = first_name
        signup_data['password'] = password
        signup_data['email'] = input_email # 更新
        request.session['biz_signup_data'] = signup_data

        return redirect('biz_business_register')
        
    return render(request, 'business/account_register.html', {'email': email})

def business_register(request):
    """画像2・3: 事業者登録（BusinessProfile作成）"""
    signup_data = request.session.get('biz_signup_data')
    if not signup_data:
        return redirect('biz_signup')

    if request.method == 'POST':
        # セッションに保存
        signup_data['business_type'] = request.POST.get('biz_type')
        signup_data['industry'] = request.POST.get('industry') # 業種も保存
        
        # 所在地情報の保存
        signup_data['biz_post_code'] = request.POST.get('post_code')
        signup_data['biz_prefecture'] = request.POST.get('prefecture')
        signup_data['biz_city'] = request.POST.get('city')
        signup_data['biz_address_line'] = request.POST.get('address_line')
        signup_data['biz_building'] = request.POST.get('building')
        
        request.session['biz_signup_data'] = signup_data
        return redirect('biz_verify')

    return render(request, 'business/business_register.html')

def verify_docs(request):
    """画像6: 書類提出"""
    # ここでもセッションチェックしても良いが、POSTのみ処理なので
    if request.method == 'POST':
        return redirect('biz_store_setup')
    return render(request, 'business/verify_docs.html')

def store_setup(request):
    """画像7: 店舗登録（Store作成）と完了処理"""
    signup_data = request.session.get('biz_signup_data')
    if not signup_data:
        # 基本的にはsignupに戻すべきだが、既存ユーザーの追加フローの場合もあり得る
        pass # ここでは新規登録フロー前提で進める

    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        post_code = request.POST.get('post_code')
        
        if not store_name:
            return render(request, 'business/store_setup.html', {'error': '店舗名を入力してください'})

        # ---- data saving ----
        # 1. User
        email = signup_data['email']
        password = signup_data['password']
        last_name = signup_data['last_name']
        first_name = signup_data['first_name']

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # 2. BusinessProfile
            company_name = last_name + "株式会社" # 簡易生成ロジック維持
            biz_profile = BusinessProfile.objects.create(
                user=user,
                company_name=company_name,
                business_type=signup_data.get('business_type', 'corporation'),
                industry=signup_data.get('industry'), # 業種保存
                # 所在地情報の保存
                post_code=signup_data.get('biz_post_code'),
                prefecture=signup_data.get('biz_prefecture'),
                city=signup_data.get('biz_city'),
                address_line=signup_data.get('biz_address_line'),
                building=signup_data.get('biz_building'),
            )
            
            # 3. Store
            Store.objects.create(
                business=biz_profile,
                store_name=store_name,
                industry=request.POST.get('industry'), # 画像準拠で追加
                post_code=post_code,
                prefecture=request.POST.get('prefecture'),
                city=request.POST.get('city'),
                address_line=request.POST.get('address_line'),
                building=request.POST.get('building'),
            )
            
            # セッションクリア
            del request.session['biz_signup_data']
            
            # 完了後、完了画面へ (ログイン画面ではなく)
            return redirect('biz_signup_complete')
            
        except Exception:
             # エラーハンドリング（重複など）
            return render(request, 'business/store_setup.html', {'error': '登録処理中にエラーが発生しました。', 'biz_data': signup_data})

            
    return render(request, 'business/store_setup.html', {'biz_data': signup_data})

def biz_signup_complete(request):
    """登録完了画面"""
    return render(request, 'business/signup_complete.html')

def biz_login(request):
    """事業者用ログイン画面"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Djangoの標準ユーザーシステムではusernameにemailを入れている前提
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('biz_portal')
        else:
            messages.error(request, "メールアドレスまたはパスワードが正しくありません。")
            return render(request, 'business/login.html', {'error': "認証に失敗しました"})
            
    return render(request, 'business/login.html')

@login_required
def biz_portal(request):
    """画像1: 企業 / 店舗一覧（ログイン後の初期画面）"""
    try:
        # プロフィールがない場合は、事業者登録画面へ誘導する
        biz_profile = BusinessProfile.objects.get(user=request.user)
    except BusinessProfile.DoesNotExist:
        return redirect('biz_business_register')

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
def template_delete(request, pk):
    """求人ひな形の削除確認・実行」"""
    template = get_object_or_404(JobTemplate, pk=pk)
    # 本来は店舗の所有権チェックが必要
    store = template.store

    if request.method == 'POST':
        template.delete()
        messages.success(request, f"「{template.title}」を削除しました。")
        return redirect('biz_template_list', store_id=store.pk)

    return render(request, 'business/template_delete_confirm.html', {
        'template': template,
        'store': store
    })

@login_required
def template_create(request, store_id):
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)

    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            # 1. テンプレートの作成
            template = JobTemplate.objects.create(
                store=store,
                title=title,
                industry=request.POST.get('industry'),
                occupation=request.POST.get('occupation'),
                work_content=request.POST.get('work_content'),
                precautions=request.POST.get('precautions'),
                # 待遇
                has_unexperienced_welcome='has_unexperienced_welcome' in request.POST,
                has_bike_car_commute='has_bike_car_commute' in request.POST,
                has_clothing_free='has_clothing_free' in request.POST,
                has_coupon_get='has_coupon_get' in request.POST,
                has_meal='has_meal' in request.POST,
                has_hair_color_free='has_hair_color_free' in request.POST,
                has_bike_bicycle_commute='has_bike_bicycle_commute' in request.POST,
                has_bicycle_commute='has_bicycle_commute' in request.POST,
                has_transportation_allowance='has_transportation_allowance' in request.POST,
                # その他
                belongings=request.POST.get('belongings'),
                requirements=request.POST.get('requirements'),
                address=request.POST.get('address'),
                access=request.POST.get('access'),
                contact_number=request.POST.get('contact_number'),
                smoking_prevention=request.POST.get('smoking_prevention', 'indoor_no_smoking'),
                has_smoking_area='has_smoking_area' in request.POST,
                requires_qualification=request.POST.get('requires_qualification') == 'true',
                qualification_id=request.POST.get('qualification_id') if request.POST.get('qualification_id') != 'none' else None,
                qualification_notes=request.POST.get('qualification_notes'),
                
                # スキルとその他条件
                skills=",".join(request.POST.getlist('skills')),
                other_conditions="\n".join([c for c in request.POST.getlist('other_conditions') if c.strip()]),

                auto_message=request.POST.get('auto_message'),
                # PDF
                manual_pdf=request.FILES.get('manual_pdf'),
            )
            
            # 2. 写真の保存（複数枚）
            photos = request.FILES.getlist('photos')
            for i, photo in enumerate(photos):
                JobTemplatePhoto.objects.create(template=template, image=photo, order=i)

            return redirect('biz_template_list', store_id=store.id)

    qualifications = QualificationMaster.objects.all().order_by('category', 'name')
    return render(request, 'business/template_form.html', {'store': store, 'qualifications': qualifications})

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
        # 待遇
        template.has_unexperienced_welcome = 'has_unexperienced_welcome' in request.POST
        template.has_bike_car_commute = 'has_bike_car_commute' in request.POST
        template.has_clothing_free = 'has_clothing_free' in request.POST
        template.has_coupon_get = 'has_coupon_get' in request.POST
        template.has_meal = 'has_meal' in request.POST
        template.has_hair_color_free = 'has_hair_color_free' in request.POST
        template.has_bike_bicycle_commute = 'has_bike_bicycle_commute' in request.POST
        template.has_bicycle_commute = 'has_bicycle_commute' in request.POST
        template.has_transportation_allowance = 'has_transportation_allowance' in request.POST
        
        template.belongings = request.POST.get('belongings')
        template.requirements = request.POST.get('requirements')
        template.address = request.POST.get('address')
        template.access = request.POST.get('access')
        template.contact_number = request.POST.get('contact_number')
        template.smoking_prevention = request.POST.get('smoking_prevention', 'indoor_no_smoking')
        template.has_smoking_area = 'has_smoking_area' in request.POST
        template.requires_qualification = request.POST.get('requires_qualification') == 'true'
        template.qualification_id = request.POST.get('qualification_id') if request.POST.get('qualification_id') != 'none' else None
        template.qualification_notes = request.POST.get('qualification_notes')

        # スキルとその他条件
        template.skills = ",".join(request.POST.getlist('skills'))
        template.other_conditions = "\n".join([c for c in request.POST.getlist('other_conditions') if c.strip()])

        template.auto_message = request.POST.get('auto_message')
        
        # PDFの更新（新しいファイルがある場合のみ）
        if 'manual_pdf' in request.FILES:
            template.manual_pdf = request.FILES['manual_pdf']
            
        template.save()

        # 写真の更新（簡易的に一度削除して再登録）
        if 'photos' in request.FILES:
            template.photos.all().delete()
            photos = request.FILES.getlist('photos')
            for i, photo in enumerate(photos):
                JobTemplatePhoto.objects.create(template=template, image=photo, order=i)

        return redirect('biz_template_list', store_id=store.id)

    qualifications = QualificationMaster.objects.all().order_by('category', 'name')
    return render(request, 'business/template_form.html', {
        'template': template, 
        'store': store, 
        'is_edit': True,
        'qualifications': qualifications
    })

# --- 求人作成フロー (画像3・4のシーケンス準拠) ---

@login_required
def job_create_from_template(request, template_pk):
    """画像1・2: ひな形を元に求人を作成(勤務日時設定)"""
    store = get_biz_context(request)
    template = get_object_or_404(JobTemplate, pk=template_pk, store=store)
    
    if request.method == 'POST':
        # セッションに一時保存して確認画面へ
        request.session['pending_job'] = {
            'template_id': template.pk,
            'work_date': request.POST.get('work_date'),
            'start_time': request.POST.get('start_time'),
            'end_time': request.POST.get('end_time'),
            'title': template.title,
            # 新規項目
            'wage': request.POST.get('wage'),
            'transport': request.POST.get('transport'),
            'visibility': request.POST.get('visibility'),
            'auto_message': request.POST.get('auto_message'),
            'msg_send': request.POST.get('msg_send') == 'true',
            'count': request.POST.get('count', 1),
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
def job_posting_detail(request, store_id, pk):
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    posting = get_object_or_404(JobPosting, pk=pk, template__store=store)
    
    return render(request, 'business/job_posting_detail.html', {
        'store': store,
        'posting': posting
    })

@login_required
def job_worker_list(request, store_id, pk):
    """マッチングしたワーカーの一覧画面（実データ反映版）"""
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    posting = get_object_or_404(JobPosting, pk=pk, template__store=store)
    
    # 申し込みデータを取得（ワーカー情報とプロフィール情報を一括取得）
    applications = JobApplication.objects.filter(job_posting=posting).select_related('worker', 'worker__workerprofile')

    # 年齢計算のロジックを各ワーカーに追加
    today = timezone.now().date()
    for app in applications:
        profile = getattr(app.worker, 'workerprofile', None)
        if profile and profile.birth_date:
            # 年齢計算
            age = today.year - profile.birth_date.year - (
                (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
            )
            app.worker_age = age
        else:
            app.worker_age = "不明"

    return render(request, 'business/job_worker_list.html', {
        'store': store,
        'posting': posting,
        'matched_workers': applications,
    })

@login_required
def job_confirm(request):
    """求人公開の確定処理（最終確認画面）"""
    pending_data = request.session.get('pending_job')
    
    # 【重要】サイドバーのURL生成に store オブジェクトが必要
    store = get_biz_context(request)
    
    # セッションデータがない場合（ブラウザバック等）の安全策
    if not pending_data:
        if store:
            return redirect('biz_template_list', store_id=store.id)
        return redirect('biz_portal')

    if request.method == 'POST':
        # チェックボックスの確認
        if 'confirm_check' in request.POST:
            # セッションデータからひな形を取得
            template = get_object_or_404(JobTemplate, pk=pending_data['template_id'])
            
            # 求人をDBに保存
            JobPosting.objects.create(
                template=template,
                title=pending_data.get('title') or template.title,
                work_date=pending_data['work_date'],
                start_time=pending_data['start_time'],
                end_time=pending_data['end_time'],
                work_content=template.work_content,
                # 新規項目
                hourly_wage=pending_data.get('wage', 1100),
                transportation_fee=pending_data.get('transport', 500),
                recruitment_count=pending_data.get('count', 1),
                break_start=pending_data.get('break_start'),
                break_duration=pending_data.get('break_duration', 0),
                visibility=pending_data.get('visibility', 'public'),
                is_published=True
            )
            
            # 完了したのでセッションを削除
            del request.session['pending_job']
            
            # 完了後の遷移先：この店舗の「求人一覧」へ
            return redirect('biz_job_posting_list', store_id=store.id)
        else:
            # チェック漏れがある場合
            return render(request, 'business/job_confirm.html', {
                'error': 'チェックがされていません。確認をお願いします。',
                'data': pending_data,
                'store': store  # ★追加
            })

    # GET時の表示
    template = None
    if pending_data:
        template = get_object_or_404(JobTemplate, pk=pending_data['template_id'])

    return render(request, 'business/job_confirm.html', {
        'data': pending_data,
        'store': store,
        'template': template
    })

@login_required
def job_worker_detail(request, store_id, worker_id):
    """ワーカー詳細画面 (店舗向け)"""
    from accounts.models import WorkerBadge  # ここでインポート
    from .models import StoreWorkerGroup, StoreWorkerMemo # ここでインポート
    
    biz_profile = get_object_or_404(BusinessProfile, user=request.user)
    store = get_object_or_404(Store, id=store_id, business=biz_profile)
    worker_user = get_object_or_404(User, id=worker_id)
    
    # ワーカーのバッジ獲得状況
    worker_badges = WorkerBadge.objects.filter(worker=worker_user.workerprofile).select_related('badge')
    
    # この店舗でのグループ設定
    groups = StoreWorkerGroup.objects.filter(store=store, worker=worker_user.workerprofile)
    
    # この店舗でのメモ
    memo = StoreWorkerMemo.objects.filter(store=store, worker=worker_user.workerprofile).first()

    return render(request, 'business/worker_detail.html', {
        'store': store,
        'worker': worker_user,
        'worker_badges': worker_badges,
        'groups': groups,
        'memo': memo,
    })