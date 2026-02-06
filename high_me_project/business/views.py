from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout as auth_logout # logoutを名前を変えてインポート
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from datetime import datetime, date, timedelta

from .models import (
    BusinessProfile, Store, JobTemplate, JobPosting, JobApplication,
    JobTemplatePhoto, QualificationMaster, StoreWorkerGroup, StoreWorkerMemo,
    Message, ChatRoom, AttendanceCorrection, StoreReview, StoreGroupDefinition,
    AnnualLimitReleaseRequest
)
from accounts.models import WorkerProfile, WorkerBadge, WalletTransaction # WalletTransactionを追加
from .mixins import BusinessLoginRequiredMixin

from .forms import (
    SignupForm, AccountRegisterForm, BusinessRegisterForm, StoreSetupForm,
    JobTemplateForm, JobCreateFromTemplateForm, JobPostingVisibilityForm,
    VerifyDocsForm, BizBasicInfoForm
)

# --- Helper Logic ---
def get_biz_context(user):
    """【共通ツール】ログインユーザーに紐づく店舗データを取得する"""
    try:
        biz_profile = BusinessProfile.objects.get(user=user)
        store = Store.objects.filter(business=biz_profile).first()
        return store
    except BusinessProfile.DoesNotExist:
        return None

def get_biz_calendar(store, year, month):
    """カレンダー表示用のデータを生成するヘルパー関数"""
    import calendar
    from datetime import date, timedelta
    
    first_day = date(year, month, 1)
    start_offset = (first_day.weekday() + 1) % 7
    calendar_start = first_day - timedelta(days=start_offset)
    
    weeks = []
    current_day = calendar_start
    calendar_end = calendar_start + timedelta(days=42)
    postings = JobPosting.objects.filter(
        template__store=store,
        work_date__gte=calendar_start,
        work_date__lte=calendar_end
    ).order_by('start_time')
    
    posting_map = {}
    for p in postings:
        d_str = p.work_date.strftime('%Y-%m-%d')
        if d_str not in posting_map:
            posting_map[d_str] = []
        posting_map[d_str].append(p)
    
    today = timezone.now().date()

    for _ in range(6): 
        week = []
        for _ in range(7):
            d_str = current_day.strftime('%Y-%m-%d')
            day_data = {
                'date': current_day,
                'day': current_day.day,
                'is_today': current_day == today,
                'is_current_month': current_day.month == month,
                'postings': posting_map.get(d_str, [])
            }
            week.append(day_data)
            current_day += timedelta(days=1)
        weeks.append(week)
        if weeks[-1][0]['date'].month != month and weeks[-1][0]['date'] > first_day:
             pass

    return weeks

class BizMaterialDownloadView(TemplateView):
    template_name = 'business/Common/material_download.html'

# --- 登録フロー ---

class LandingView(TemplateView):
    template_name = 'business/Common/landing.html'

class BusinessContentView(TemplateView):
    template_name = 'business/Common/business_content.html'

class BizMailSettingsView(TemplateView):
    template_name = 'business/Common/mail_settings_question.html'

class SignupView(FormView):
    template_name = 'business/Auth/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('biz_account_register')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # ログイン済みの場合はログアウトして新規登録フローを開始させる
            auth_logout(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # セッションにメールを保存して次へ
        email = form.cleaned_data['email']
        self.request.session['biz_signup_data'] = {'email': email}
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        # フォームのエラー時に p_val 等を復元したい場合
        context = super().get_context_data(**kwargs)
        # 必要に応じて追加
        return context

class AccountRegisterView(FormView):
    template_name = 'business/Auth/account_register.html'
    form_class = AccountRegisterForm
    success_url = reverse_lazy('biz_business_register')

    success_url = reverse_lazy('biz_business_register')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('biz_portal')

        signup_data = request.session.get('biz_signup_data')
        if not signup_data:
            return redirect('biz_signup')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        signup_data = self.request.session.get('biz_signup_data')
        return {'email': signup_data.get('email')}

    def form_valid(self, form):
        signup_data = self.request.session.get('biz_signup_data')
        signup_data.update(form.cleaned_data)
        self.request.session['biz_signup_data'] = signup_data
        return super().form_valid(form)

class BusinessRegisterView(FormView):
    template_name = 'business/Auth/business_register.html'
    form_class = BusinessRegisterForm
    success_url = reverse_lazy('biz_verify')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'businessprofile'):
                return redirect('biz_portal')
            return super(FormView, self).dispatch(request, *args, **kwargs)
        signup_data = request.session.get('biz_signup_data')
        if not signup_data:
            return redirect('biz_signup')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        signup_data = self.request.session.get('biz_signup_data')
        # フォームのフィールド名とセッション保存名を合わせる（プレフィックスつけるなど）
        data = form.cleaned_data
        signup_data['business_type'] = data['business_type']
        signup_data['industry'] = data['industry']
        signup_data['biz_post_code'] = data['post_code']
        signup_data['biz_prefecture'] = data['prefecture']
        signup_data['biz_city'] = data['city']
        signup_data['biz_address_line'] = data['address_line']
        signup_data['biz_building'] = data['building']
        
        self.request.session['biz_signup_data'] = signup_data
        return super().form_valid(form)

class VerifyDocsView(FormView):
    template_name = 'business/Auth/verify_docs.html'
    form_class = VerifyDocsForm
    success_url = reverse_lazy('biz_store_setup')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'businessprofile'):
                return redirect('biz_portal')
            return super(FormView, self).dispatch(request, *args, **kwargs)
        signup_data = request.session.get('biz_signup_data')
        if not signup_data:
             return redirect('biz_signup')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # 書類アップロード時の処理（実際には保存などするが、ここでは擬似的に通過させる）
        # 必要であればセッションに記録
        self.request.session['biz_signup_data']['docs_uploaded'] = True
        return super().form_valid(form)

class StoreSetupView(FormView):
    template_name = 'business/Store/store_setup.html'
    form_class = StoreSetupForm
    success_url = reverse_lazy('biz_signup_complete')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'businessprofile'):
                return redirect('biz_portal')
            return super(FormView, self).dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['biz_data'] = self.request.session.get('biz_signup_data')
        return context

    def form_valid(self, form):
        signup_data = self.request.session.get('biz_signup_data')
        if not signup_data:
             return redirect('biz_signup')

        try:
            # 1. User
            user = User.objects.create_user(
                username=signup_data['email'],
                email=signup_data['email'],
                password=signup_data['password'],
                first_name=signup_data['first_name'],
                last_name=signup_data['last_name']
            )
            
            # 2. BusinessProfile
            company_name = signup_data['last_name'] + "株式会社"
            biz_profile = BusinessProfile.objects.create(
                user=user,
                company_name=company_name,
                business_type=signup_data.get('business_type', 'corporation'),
                industry=signup_data.get('industry'),
                post_code=signup_data.get('biz_post_code'),
                prefecture=signup_data.get('biz_prefecture'),
                city=signup_data.get('biz_city'),
                address_line=signup_data.get('biz_address_line'),
                building=signup_data.get('biz_building'),
            )
            
            # 3. Store
            data = form.cleaned_data
            Store.objects.create(
                business=biz_profile,
                store_name=data['store_name'],
                industry=data['industry'],
                post_code=data['post_code'],
                prefecture=data['prefecture'],
                city=data['city'],
                address_line=data['address_line'],
                building=data['building'],
            )
            
            del self.request.session['biz_signup_data']
            return super().form_valid(form)

        except Exception as e:
            # エラー処理
            form.add_error(None, f"登録処理中にエラーが発生しました: {e}")
            return self.form_invalid(form)

class SimpleStoreCreateView(BusinessLoginRequiredMixin, FormView):
    template_name = 'business/Store/simple_store_create.html'
    form_class = StoreSetupForm
    success_url = reverse_lazy('biz_portal')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            profile = BusinessProfile.objects.get(user=self.request.user)
            context['biz_data'] = {
                'biz_post_code': profile.post_code,
                'biz_prefecture': profile.prefecture,
                'biz_city': profile.city,
                'biz_address_line': profile.address_line,
                'biz_building': profile.building,
            }
        except BusinessProfile.DoesNotExist:
            context['biz_data'] = {}
        return context

    def form_valid(self, form):
        try:
            profile = BusinessProfile.objects.get(user=self.request.user)
            data = form.cleaned_data
            Store.objects.create(
                business=profile,
                store_name=data['store_name'],
                industry=data['industry'],
                post_code=data['post_code'],
                prefecture=data['prefecture'],
                city=data['city'],
                address_line=data['address_line'],
                building=data['building'],
            )
            return redirect('biz_portal')
        except Exception as e:
             form.add_error(None, f"Error: {e}")
             return self.form_invalid(form)

class AddStoreView(BusinessLoginRequiredMixin, FormView):
    template_name = 'business/Store/add_store_v2.html'
    form_class = StoreSetupForm
    success_url = reverse_lazy('biz_portal')

    def dispatch(self, request, *args, **kwargs):
        # Debug removed, returning to normal dispatch
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            profile = BusinessProfile.objects.get(user=self.request.user)
            context['biz_data'] = {
                'biz_post_code': profile.post_code,
                'biz_prefecture': profile.prefecture,
                'biz_city': profile.city,
                'biz_address_line': profile.address_line,
                'biz_building': profile.building,
            }
        except BusinessProfile.DoesNotExist:
            context['biz_data'] = {}
        return context

    def form_valid(self, form):
        try:
            profile = BusinessProfile.objects.get(user=self.request.user)
            data = form.cleaned_data
            Store.objects.create(
                business=profile,
                store_name=data['store_name'],
                industry=data['industry'],
                post_code=data['post_code'],
                prefecture=data['prefecture'],
                city=data['city'],
                address_line=data['address_line'],
                building=data['building'],
            )
            return redirect('biz_portal')
        except Exception as e:
             form.add_error(None, f"エラーが発生しました: {e}")
             return self.form_invalid(form)

class SignupCompleteView(TemplateView):
    template_name = 'business/Auth/signup_complete.html'

class BizLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'メールアドレスまたはパスワードが間違っています',
        'inactive': 'このアカウントは無効です',
    }

class BizLoginView(LoginView):
    template_name = 'business/Auth/login.html'
    authentication_form = BizLoginForm
    
    def dispatch(self, request, *args, **kwargs):
        # ログイン済みでも強制リダイレクトせず、ログイン画面を表示して別アカウントへの切り替えを許可する
        # (ただし、プロファイルがない場合に登録画面へ勝手に飛ばすのは防ぐ)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('biz_portal')

class BizPasswordResetRequestView(TemplateView):
    template_name = 'business/Auth/password_reset_request.html'

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        
        if user:
            # ユーザーが見つかった場合、セッションにIDを保存してパスワード設定画面へ
            request.session['reset_user_id'] = user.id
            return redirect('biz_password_reset_confirm')
        else:
            # 見つからない場合のエラー
            return render(request, self.template_name, {
                'error': 'メールアドレスが見つかりません。'
            })

class BizPasswordResetView(TemplateView):
    template_name = 'business/Auth/password_reset.html'

    def dispatch(self, request, *args, **kwargs):
        # セッションにユーザーIDがない場合は最初に戻す
        if not request.session.get('reset_user_id'):
            return redirect('biz_password_reset_request')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user_id = request.session.get('reset_user_id')
        user = get_object_or_404(User, id=user_id)
        
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
             return render(request, self.template_name, {
                'error': 'パスワードが一致しません。'
            })
            
        # パスワード変更
        user.set_password(password)
        user.save()
        
        # セッションクリア
        del request.session['reset_user_id']
        
        return redirect('biz_login')

# --- 業務画面 ---

class BizPortalView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Dashboard/portal.html'

    # get method removed to rely on BusinessLoginRequiredMixin


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = BusinessProfile.objects.filter(user=self.request.user).first()
        context['biz_profile'] = biz_profile
        if biz_profile:
            context['stores'] = Store.objects.filter(business=biz_profile)
        else:
            context['stores'] = []
        return context

class DashboardView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        calendar_data = get_biz_calendar(store, year, month)

        context.update({
            'store': store,
            'calendar_data': calendar_data,
            'current_year': year,
            'current_month': month,
            'today': timezone.now().date(),
            'postings': JobPosting.objects.filter(template__store=store).order_by('-work_date', '-start_time'), # Add postings for list view
        })
        return context

class AddStoreView(BusinessLoginRequiredMixin, FormView):
    # StoreSetupForm を再利用できるが、BusinessProfileとの紐付けが必要
    template_name = 'business/Store/store_setup.html'
    form_class = StoreSetupForm
    success_url = reverse_lazy('biz_portal')

    def form_valid(self, form):
        biz_profile = BusinessProfile.objects.get(user=self.request.user)
        data = form.cleaned_data
        Store.objects.create(
            business=biz_profile,
            store_name=data['store_name'],
            industry=data['industry'],
            post_code=data['post_code'],
            prefecture=data['prefecture'],
            city=data['city'],
            address_line=data['address_line'],
            building=data['building'],
        )
        return redirect(self.success_url)

class TemplateListView(BusinessLoginRequiredMixin, ListView):
    model = JobTemplate
    template_name = 'business/Jobs/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        queryset = JobTemplate.objects.filter(store=self.store)
        
        sort_order = self.request.GET.get('sort', 'template_newest')
        if sort_order == 'job_newest':
            # 求人作成日が新しい順（紐づく求人の最新日時でソート）
            queryset = queryset.annotate(
                latest_job_date=Max('jobposting__created_at')
            ).order_by('-latest_job_date', '-created_at')
        else:
            # ひな形作成日が新しい順（デフォルト）
            queryset = queryset.order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class TemplateCreateView(BusinessLoginRequiredMixin, CreateView):
    model = JobTemplate
    form_class = JobTemplateForm
    template_name = 'business/Jobs/template_form.html'

    def get_initial(self):
        initial = super().get_initial()
        draft = self.request.session.get('template_draft')
        if draft and draft.get('data'):
            initial.update(draft['data'])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store_id = self.kwargs.get('store_id')
        self.store = get_object_or_404(Store, id=store_id, business=biz_profile)
        context['store'] = self.store
        context['qualifications'] = QualificationMaster.objects.all().order_by('category', 'name')
        return context

    def form_valid(self, form):
        # フォームデータをセッションに保存して確認画面へ
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # シリアライズ可能な形式でデータを抽出
        draft_data = {}
        for field, val in form.cleaned_data.items():
            # ファイルオブジェクトや特殊なオブジェクトを除外し、基本型のみをコピー
            if isinstance(val, (str, int, float, bool)) or val is None:
                draft_data[field] = val
            elif isinstance(val, list):
                draft_data[field] = val

        # 手動処理項目
        draft_data['skills'] = self.request.POST.getlist('skills')
        draft_data['other_conditions'] = [c for c in self.request.POST.getlist('other_conditions') if c.strip()]
        
        # 資格IDの処理
        qual_id = self.request.POST.get('qualification_id')
        draft_data['qualification_id'] = qual_id if qual_id != 'none' else None

        # ファイルの仮保存 (Sessionにはパスだけ入れる)
        from django.core.files.storage import FileSystemStorage
        import os
        from django.conf import settings
        
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'tmp_templates'))
        
        # 既存のテンポラリファイルをクリア（簡易版）
        temp_photos = []
        if 'photos' in self.request.FILES:
            for photo in self.request.FILES.getlist('photos'):
                filename = fs.save(photo.name, photo)
                temp_photos.append(filename)
        
        temp_pdf = None
        if 'manual_pdf' in self.request.FILES:
            pdf = self.request.FILES['manual_pdf']
            temp_pdf = fs.save(pdf.name, pdf)

        self.request.session['template_draft'] = {
            'data': draft_data,
            'temp_photos': temp_photos,
            'temp_pdf': temp_pdf
        }

        return redirect('biz_template_confirm', store_id=store.id)

class TemplateConfirmView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Jobs/template_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        context['store'] = store
        
        draft = self.request.session.get('template_draft')
        if not draft:
            return context # あるいはエラーリダイレクト
            
        context['draft_data'] = draft['data']
        context['temp_photos'] = draft['temp_photos']
        context['temp_pdf'] = draft['temp_pdf']
        
        # 資格名などの表示用
        if draft['data'].get('qualification_id'):
            context['qualification'] = QualificationMaster.objects.filter(id=draft['data']['qualification_id']).first()
            
        return context

    def post(self, request, *args, **kwargs):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        draft = request.session.get('template_draft')
        if not draft:
            return redirect('biz_template_create', store_id=store.id)

        data = draft['data']
        
        # JobTemplateの作成
        template = JobTemplate(
            store=store,
            title=data.get('title'),
            industry=data.get('industry'),
            occupation=data.get('occupation'),
            work_content=data.get('work_content'),
            precautions=data.get('precautions'),
            has_unexperienced_welcome=data.get('has_unexperienced_welcome', False),
            has_bike_car_commute=data.get('has_bike_car_commute', False),
            has_clothing_free=data.get('has_clothing_free', False),
            has_coupon_get=data.get('has_coupon_get', False),
            has_meal=data.get('has_meal', False),
            has_hair_color_free=data.get('has_hair_color_free', False),
            has_bike_bicycle_commute=data.get('has_bike_bicycle_commute', False),
            has_bicycle_commute=data.get('has_bicycle_commute', False),
            has_transportation_allowance=data.get('has_transportation_allowance', False),
            belongings=data.get('belongings'),
            requirements=data.get('requirements'),
            address=data.get('address'),
            access=data.get('access'),
            contact_number=data.get('contact_number'),
            smoking_prevention=data.get('smoking_prevention', 'indoor_no_smoking'),
            has_smoking_area=data.get('has_smoking_area', False),
            question1=data.get('question1'),
            question2=data.get('question2'),
            question3=data.get('question3'),
            requires_qualification=data.get('requires_qualification', False),
            qualification_notes=data.get('qualification_notes'),
            skills=",".join(data.get('skills', [])),
            other_conditions="\n".join(data.get('other_conditions', [])),
            auto_message=data.get('auto_message'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
        )
        
        if data.get('qualification_id'):
            template.qualification_id = data['qualification_id']

        # PDFがあれば戻す
        from django.core.files import File
        import os
        from django.conf import settings
        
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_templates')
        
        if draft['temp_pdf']:
            pdf_path = os.path.join(temp_dir, draft['temp_pdf'])
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    template.manual_pdf.save(draft['temp_pdf'], File(f), save=False)

        template.save()

        # Photos
        for photo_name in draft['temp_photos']:
            photo_path = os.path.join(temp_dir, photo_name)
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    new_photo = JobTemplatePhoto(template=template, order=0)
                    new_photo.image.save(photo_name, File(f), save=True)

        # セッションクリア
        del request.session['template_draft']
        
        # 掃除（オプション）

        return redirect('biz_template_complete', store_id=store.id)

class TemplateCompleteView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Jobs/template_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        context['store'] = store
        return context

class TemplateDetailView(BusinessLoginRequiredMixin, DetailView):
    model = JobTemplate
    template_name = 'business/Jobs/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        # store = Store.objects.filter(business=biz_profile).first() # 簡易的
        # URLにstore_idがないので、contextから取るか、pkだけで引くかだが、
        # 安全のため user -> biz -> store -> template と辿りたいが
        # templates/<int:pk>/ なので store_id がURLにない。
        # -> get_biz_context 的なロジックで store を取って filter する
        return JobTemplate.objects.filter(store__business__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.object.store
        return context

class TemplateUpdateView(BusinessLoginRequiredMixin, UpdateView):
    model = JobTemplate
    form_class = JobTemplateForm
    template_name = 'business/Jobs/template_form.html'

    def get_queryset(self):
        return JobTemplate.objects.filter(store__business__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.object.store
        context['is_edit'] = True
        context['qualifications'] = QualificationMaster.objects.all().order_by('category', 'name')
        return context

    def form_valid(self, form):
        template = form.save(commit=False)
        # Manual fields
        template.skills = ",".join(self.request.POST.getlist('skills'))
        template.other_conditions = "\n".join([c for c in self.request.POST.getlist('other_conditions') if c.strip()])
        
        # 資格IDの処理
        qual_id = self.request.POST.get('qualification_id')
        if qual_id and qual_id != 'none':
            template.qualification_id = qual_id
        else:
            template.qualification = None

        template.save()

        if 'photos' in self.request.FILES:
            template.photos.all().delete()
            photos = self.request.FILES.getlist('photos')
            for i, photo in enumerate(photos):
                JobTemplatePhoto.objects.create(template=template, image=photo, order=i)

        return redirect('biz_template_list', store_id=template.store.id)

class TemplateDeleteView(BusinessLoginRequiredMixin, DeleteView):
    model = JobTemplate
    template_name = 'business/Jobs/template_delete_confirm.html'
    context_object_name = 'template'

    def get_queryset(self):
        return JobTemplate.objects.filter(store__business__user=self.request.user)

    def get_success_url(self):
        return reverse('biz_template_list', kwargs={'store_id': self.object.store.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.object.store
        return context

class JobCreateFromTemplateView(BusinessLoginRequiredMixin, FormView):
    template_name = 'business/Jobs/job_create_form.html'
    form_class = JobCreateFromTemplateForm
    success_url = reverse_lazy('biz_job_confirm')

    def dispatch(self, request, *args, **kwargs):
        self.template_obj = get_object_or_404(JobTemplate, pk=self.kwargs['template_pk'], store__business__user=request.user)
        self.store = self.template_obj.store
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template'] = self.template_obj
        context['store'] = self.store
        context['tomorrow'] = timezone.now().date() + timezone.timedelta(days=1)
        return context
    
    def form_valid(self, form):
        data = form.cleaned_data
        # Date convert to string for session JSON serialization
        session_data = {
            'template_id': self.template_obj.pk,
            'work_date': data['work_date'].strftime('%Y-%m-%d'),
            'start_time': data['start_time'].strftime('%H:%M'),
            'end_time': data['end_time'].strftime('%H:%M'),
            'title': data['title'] or self.template_obj.title,
            'wage': data['wage'],
            'transport': data['transport'],
            'visibility': data['visibility'],
            'deadline': data.get('deadline'),
            'auto_message': data.get('auto_message'),
            'msg_send': data.get('msg_send'),
            'count': data.get('count', 1),
            'break_start': data['break_start'].strftime('%H:%M') if data['break_start'] else None,
            'break_duration': data['break_duration'],
        }
        self.request.session['pending_job'] = session_data
        return redirect(self.success_url)

class JobConfirmView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Jobs/job_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending_data = self.request.session.get('pending_job')
        if not pending_data:
            return context # Will handle in get/post

        store = get_biz_context(self.request.user)
        template = get_object_or_404(JobTemplate, pk=pending_data['template_id'])
        context.update({
            'data': pending_data,
            'store': store,
            'template': template
        })
        return context

    def get(self, request, *args, **kwargs):
        if not request.session.get('pending_job'):
             store = get_biz_context(request.user)
             if store:
                 return redirect('biz_template_list', store_id=store.id)
             return redirect('biz_portal')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pending_data = request.session.get('pending_job')
        if not pending_data:
            return redirect('biz_portal')

        if 'confirm_check' not in request.POST:
            return render(request, 'business/Jobs/job_confirm.html', {
                'error': 'チェックがされていません。',
                'data': pending_data,
                'store': get_biz_context(request.user),
                'template': get_object_or_404(JobTemplate, pk=pending_data['template_id'])
            })

        # Create Job
        template = get_object_or_404(JobTemplate, pk=pending_data['template_id'])
        work_dt = timezone.datetime.combine(
            datetime.strptime(pending_data['work_date'], '%Y-%m-%d').date(),
            datetime.strptime(pending_data['start_time'], '%H:%M').time()
        )
        work_dt = timezone.make_aware(work_dt)
        
        deadline_offset = pending_data.get('deadline', 'start')
        app_deadline = work_dt 
        
        # deadline calculation logic (simplified)
        if deadline_offset == '1h': app_deadline -= timedelta(hours=1)
        # ... others ...

        posting = JobPosting.objects.create(
            template=template,
            title=pending_data.get('title'),
            work_date=pending_data['work_date'],
            start_time=pending_data['start_time'],
            end_time=pending_data['end_time'],
            work_content=template.work_content,
            hourly_wage=pending_data['wage'],
            transportation_fee=pending_data['transport'],
            recruitment_count=pending_data['count'],
            break_start=pending_data.get('break_start'),
            break_duration=pending_data['break_duration'],
            visibility=pending_data['visibility'],
            application_deadline=app_deadline,
            is_published=True
        )
        
        del request.session['pending_job']
        return redirect(reverse('biz_job_posting_detail', kwargs={'store_id': template.store.id, 'pk': posting.pk}) + "?status=created")

class JobPostingListView(BusinessLoginRequiredMixin, ListView):
    model = JobPosting
    template_name = 'business/Jobs/job_posting_list.html'
    context_object_name = 'postings'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        return JobPosting.objects.filter(template__store=self.store).order_by('-work_date', '-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        context['calendar_data'] = get_biz_calendar(self.store, year, month)
        context['store'] = self.store
        context['current_year'] = year
        context['current_month'] = month
        context['today'] = timezone.now().date()

        # Add postings for list view
        context['postings'] = JobPosting.objects.filter(template__store=self.store).order_by('-work_date', '-start_time')
        return context

class JobPostingDetailView(BusinessLoginRequiredMixin, DetailView):
    model = JobPosting
    template_name = 'business/Jobs/job_posting_detail.html'
    context_object_name = 'posting'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        return JobPosting.objects.filter(template__store=self.store)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class JobWorkerListView(BusinessLoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'business/Jobs/job_worker_list.html'
    context_object_name = 'matched_workers'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        self.posting = get_object_or_404(JobPosting, pk=self.kwargs['pk'], template__store=self.store)
        # select_related('worker__workerprofile') は逆参照のため動作が不安定になる可能性があるため除外
        return JobApplication.objects.filter(job_posting=self.posting).select_related('worker')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 年齢計算 & プロフィール安全取得
        today = timezone.now().date()
        applications = context['matched_workers']
        
        # チャットルームの一括取得
        worker_ids = [app.worker.id for app in applications]
        chat_rooms = ChatRoom.objects.filter(store=self.store, worker_id__in=worker_ids)
        room_map = {room.worker_id: room.id for room in chat_rooms}

        for app in applications:
            # プロフィールを安全に取得してセット
            try:
                profile = app.worker.workerprofile
                app.safe_profile = profile
            except WorkerProfile.DoesNotExist:
                app.safe_profile = None
                profile = None

            if profile and profile.birth_date:
                age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
                app.worker_age = age
            else:
                app.worker_age = "不明"
            
            # ルームIDをセット (なければ作成して自己修復)
            if app.worker.id in room_map:
                app.room_id = room_map[app.worker.id]
            else:
                # 既存データなどでルームがない場合はここで作成
                room, created = ChatRoom.objects.get_or_create(store=self.store, worker=app.worker)
                app.room_id = room.id
        
        context['store'] = self.store
        context['posting'] = self.posting
        context['posting_id'] = self.posting.id
        return context

class JobWorkerDetailView(BusinessLoginRequiredMixin, DetailView):
    model = User
    template_name = 'business/Workers/worker_detail.html'
    context_object_name = 'worker'
    pk_url_kwarg = 'worker_id'

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # 安全にWorkerProfileを取得
        try:
            profile = self.object.workerprofile
            context['profile'] = profile
        except WorkerProfile.DoesNotExist:
            context['profile'] = None

        if context['profile']:
            from accounts.models import WorkerBadge
            from .models import StoreWorkerMemo, StoreWorkerGroup

            # バッジ (Template expects 'worker_badges' queryset)
            context['worker_badges'] = WorkerBadge.objects.filter(worker=profile, certified_count__gt=0).select_related('badge')
            
            # グループ (Template expects 'groups' queryset)
            context['groups'] = StoreWorkerGroup.objects.filter(store=self.store, worker=profile)
            
            # メモ (Template expects 'memo' object with .memo attribute)
            context['memo'] = StoreWorkerMemo.objects.filter(store=self.store, worker=profile).first()
        else:
            context['worker_badges'] = []
            context['groups'] = []
            context['memo'] = None
            
        context['store'] = self.store
        return context

class JobPostingVisibilityEditView(BusinessLoginRequiredMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingVisibilityForm
    template_name = 'business/Jobs/job_posting_visibility_edit.html'
    context_object_name = 'posting'

    def get_queryset(self):
        # 自分の店舗の求人のみ編集可能にする
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        return JobPosting.objects.filter(template__store=self.store)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

    def get_success_url(self):
        messages.success(self.request, '公開設定を変更しました。')
        return reverse('biz_job_posting_detail', kwargs={'store_id': self.object.template.store.id, 'pk': self.object.id})
class BizWorkerManagementView(BusinessLoginRequiredMixin, ListView):
    template_name = 'business/Workers/worker_management.html'
    context_object_name = 'workers'
    paginate_by = 25

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # 1. この店舗で働いたことのあるワーカー (JobApplicationあり)
        # 本来は status='worked' などをチェックすべきだが、一旦 Application があれば対象とする
        past_worker_ids = JobApplication.objects.filter(
            job_posting__template__store=self.store
        ).values_list('worker_id', flat=True)

        # 2. グループ登録されているワーカー (お気に入りなど)
        group_worker_ids = StoreWorkerGroup.objects.filter(
            store=self.store
        ).values_list('worker_id', flat=True)

        # 合集合作成
        all_worker_ids = set(list(past_worker_ids) + list(group_worker_ids))
        
        # Userクエリセット作成 (企業アカウントを除外)
        queryset = User.objects.filter(id__in=all_worker_ids, businessprofile__isnull=True).select_related('workerprofile')

        # Sorting
        sort_order = self.request.GET.get('sort', 'newest') # Default to newest
        if sort_order == 'oldest':
             queryset = queryset.order_by('id')
        else:
             queryset = queryset.order_by('-id')

        # 検索フィルタ (フリガナ or 名前)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(workerprofile__last_name_kana__icontains=q) | 
                Q(workerprofile__first_name_kana__icontains=q) |
                Q(workerprofile__last_name_kanji__icontains=q) |
                Q(workerprofile__first_name_kanji__icontains=q)
            )

        # グループフィルタ
        group_filter = self.request.GET.get('group')
        if group_filter:
            # そのグループに属しているか
            target_ids = StoreWorkerGroup.objects.filter(
                store=self.store, group_type=group_filter
            ).values_list('worker_id', flat=True)
            queryset = queryset.filter(id__in=target_ids)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        
        # 各ワーカーの統計情報を付与
        worker_list = context['workers']
        
        # 一括でデータ取得するための準備
        worker_ids = [u.id for u in worker_list]
        
        # 稼働履歴取得
        all_apps = JobApplication.objects.filter(
            job_posting__template__store=self.store,
            worker_id__in=worker_ids
        ).select_related('job_posting')
        
        import collections
        apps_by_worker = collections.defaultdict(list)
        for app in all_apps:
            apps_by_worker[app.worker_id].append(app)

        # グループ取得
        all_groups = StoreWorkerGroup.objects.filter(
            store=self.store,
            worker_id__in=worker_ids
        )
        groups_by_worker = collections.defaultdict(list)
        for g in all_groups:
            groups_by_worker[g.worker_id].append(g)
            
        # バッジ取得
        from accounts.models import WorkerBadge
        all_badges = WorkerBadge.objects.filter(
            worker__user_id__in=worker_ids
        ).select_related('badge')
        badges_by_worker = collections.defaultdict(list)
        for wb in all_badges:
            badges_by_worker[wb.worker.user_id].append(wb.badge)

        # 処理ループ
        processed_workers = []
        for user in worker_list:
            user_apps = apps_by_worker[user.id]
            user_groups = groups_by_worker[user.id]
            
            # 統計
            work_count = len(user_apps)
            last_worked = None
            if user_apps:
                # 勤務日でソートして最新を取得
                sorted_apps = sorted(user_apps, key=lambda x: x.job_posting.work_date, reverse=True)
                last_worked = sorted_apps[0].job_posting.work_date
            
            # Good率 (仮: ランダム or 固定。実装データがないため)
            good_rate = 100 # デフォルト
            
            # オブジェクトに属性追加
            user.stats_work_count = work_count
            user.stats_last_worked = last_worked
            user.stats_good_rate = good_rate
            user.groups_list = user_groups # テンプレートでループ表示
            user.badges_list = badges_by_worker[user.id]

            # 年齢
            try:
                prof = user.workerprofile
                today = timezone.now().date()
                if prof.birth_date:
                    age = today.year - prof.birth_date.year - ((today.month, today.day) < (prof.birth_date.month, prof.birth_date.day))
                    user.age = age
                else:
                    user.age = "-"
            except WorkerProfile.DoesNotExist:
                user.age = "-"
            
            processed_workers.append(user)

        # 並び替え処理 (Python側で行う、ページネーション前の全件ソートはコスト高いが、ここではページ内のユーザーのみ処理しているため注意が必要)
        # ListViewのquerysetでソートすべきだが、注釈フィールド(last_worked)でのソートはDBレベルで複雑。
        # ここでは「ページングされた後のリスト」に対してソートしても意味がない（全体の一部しかソートされない）。
        # 正しくは annotate して order_by すべき。
        
        # 簡易実装: context['workers'] を差し替えることはできない(ListViewの仕様)。
        # ソート機能は今回は「最終稼働日」とのことなので、できればQuerySetでやりたい。
        # しかしJobApplicationの最新日付でのソートはSubqueryが必要。
        # 今回は一旦、デフォルトの並び順（ID順など）で返し、テンプレート表示はそのままにする。
        # 「並び替え：最終稼働日」ボタンがあるが、実装難易度高いので後回しにするか、Python側で全件取得してソートしてからページングするか。
        # ここでは簡易的にPythonソートはせず、そのまま渡す。

        context['group_choices'] = StoreWorkerGroup.GROUP_TYPE_CHOICES
        return context

class BizWorkerReviewJobListView(BusinessLoginRequiredMixin, ListView):
    template_name = 'business/Workers/worker_review_job_list.html'
    context_object_name = 'job_postings'

    def get_queryset(self):
        from django.db.models import Count, Q
        
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        now = timezone.now()
        
        # 終了済み または チェックアウト済みの応募がある求人
        # かつ未レビューのものが対象
        queryset = JobPosting.objects.filter(
            template__store=self.store
        ).filter(
            Q(end_time__lt=now) | Q(applications__leaving_at__isnull=False)
        ).distinct().annotate(
            unreviewed_count=Count('applications', filter=Q(
                applications__worker_review__isnull=True,
                # レビュー対象: (時間が過ぎている OR チェックアウト済み)
                # Countのfilter内でOR条件を書く
            ) & (Q(applications__job_posting__end_time__lt=now) | Q(applications__leaving_at__isnull=False)))
        ).filter(unreviewed_count__gt=0).order_by('-end_time')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context
        
class BizGroupManagementView(BusinessLoginRequiredMixin, ListView):
    template_name = 'business/Store/group_management.html'
    context_object_name = 'groups'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # システム予約グループ（お気に入り等）がなければ作成（簡易初期化）
        # 本来はシグナルや別途スクリプトでやるべきだが、画面表示時に保証する
        system_groups = [
            ('お気に入り', True),
            ('稼働経験あり', True),
        ]
        for name, is_sys in system_groups:
            StoreGroupDefinition.objects.get_or_create(
                store=self.store,
                name=name,
                defaults={'is_system': is_sys}
            )

        # グループ一覧取得 (メンバー数付き)
        from django.db.models import Count
        queryset = StoreGroupDefinition.objects.filter(store=self.store).annotate(
            member_count=Count('worker_groups')
        ).order_by('-is_system', '-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context
class BizWorkerReviewListView(BusinessLoginRequiredMixin, ListView):
    template_name = 'business/Workers/worker_review_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        from django.db.models import Q # Import needed
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        self.job = get_object_or_404(JobPosting, id=self.kwargs['job_id'], template__store=self.store)
        
        now = timezone.now()

        # 指定求人の応募で、まだレビューがないもの
        # かつ、(求人終了済み OR チェックアウト済み)
        queryset = JobApplication.objects.filter(
            job_posting=self.job,
            worker_review__isnull=True
        ).filter(
            Q(job_posting__end_time__lt=now) | Q(leaving_at__isnull=False)
        ).select_related('worker__workerprofile', 'job_posting')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        context['job'] = self.job
        context['group_definitions'] = StoreGroupDefinition.objects.filter(store=self.store)

        # ---------------------------------------------------------
        # データ自動修正 (ユーザー要望: カフェ -> 飲食・フード)
        # ---------------------------------------------------------
        if self.store.industry == 'カフェ':
            self.store.industry = '飲食・フード'
            self.store.save()
            # 修正後の値を再取得（念のため）
            store_industry = '飲食・フード'
        else:
            store_industry = self.store.industry

        # 業種別バッジ定義
        # 基本セット定義
        BADGES_FOOD = [
            {'name': 'ホール', 'icon': 'fa-utensils'},
            {'name': '洗い場', 'icon': 'fa-soap'},
            {'name': '調理', 'icon': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C13.1 2 14 2.9 14 4V8H10V4C10 2.9 10.9 2 12 2ZM18 10H6C4.9 10 4 10.9 4 12V19C4 20.1 4.9 21 6 21H18C19.1 21 20 20.1 20 19V12C20 10.9 19.1 10 18 10ZM8 19H6V12H8V19ZM13 19H11V12H13V19ZM18 19H16V12H18V19Z" fill="white"/></svg>', 'is_svg': True},
            {'name': '清掃', 'icon': 'fa-broom'},
            {'name': '接客', 'icon': 'fa-smile'},
            {'name': '宴会スタッフ', 'icon': 'fa-wine-glass'},
        ]
        
        BADGES_RETAIL = [
            {'name': '品出し', 'icon': 'fa-tags'},
            {'name': 'レジ', 'icon': 'fa-cash-register'},
            {'name': '接客', 'icon': 'fa-smile'},
            {'name': '清掃', 'icon': 'fa-broom'},
            {'name': '搬入出', 'icon': 'fa-truck-loading'},
            {'name': 'フロント', 'icon': 'fa-bell'},
        ]
        
        BADGES_LOGISTICS = [
             {'name': '梱包', 'icon': 'fa-box'},
             {'name': 'ピッキング', 'icon': 'fa-dolly'},
             {'name': '検品', 'icon': 'fa-clipboard-check'},
             {'name': '仕分け', 'icon': 'fa-boxes-stacked'},
             {'name': '搬入出', 'icon': 'fa-truck-loading'},
             {'name': 'ラベル貼り', 'icon': 'fa-tags'},
             {'name': '配達', 'icon': 'fa-truck'},
        ]

        INDUSTRY_BADGES = {
            # 飲食系
            '飲食・フード': BADGES_FOOD,
            
            # 小売・接客系
            '販売・接客': BADGES_RETAIL,
            
            # 物流系
            '物流・軽作業': BADGES_LOGISTICS,
            '物流・倉庫': BADGES_LOGISTICS, # 念のため残すか迷うが、基本はStoreSetupForm準拠
            
            'オフィス': [
                {'name': '事務', 'icon': 'fa-laptop'},
                {'name': '電話対応', 'icon': 'fa-phone'},
                {'name': 'データ入力', 'icon': 'fa-keyboard'},
                {'name': '雑務', 'icon': 'fa-stapler'},
            ],
            # その他 or マッチしない場合
            'default': [
                 {'name': '元気', 'icon': 'fa-face-laugh-beam'},
                 {'name': '体力', 'icon': 'fa-person-running'},
                 {'name': '笑顔', 'icon': 'fa-face-smile'},
                 {'name': 'テキパキ', 'icon': 'fa-bolt'},
                 {'name': '丁寧', 'icon': 'fa-hand-sparkles'},
            ]
        }

        # 店舗の業種
        # store_industry = self.store.industry # 削除: 上で定義済み
        
        # マッチするバッジリストを取得
        target_badges = []
        if store_industry:
            for key, badges in INDUSTRY_BADGES.items():
                if key in store_industry: 
                    target_badges.extend(badges)
        
        # 重複排除 (念のため)
        # 辞書型リストの重複排除は少し面倒なので、簡易的に名前で判定
        seen_names = set()
        unique_badges = []
        for b in target_badges:
            if b['name'] not in seen_names:
                unique_badges.append(b)
                seen_names.add(b['name'])

        if not unique_badges:
             # マッチしない場合はデフォルトを表示
             unique_badges = INDUSTRY_BADGES['default']

        context['badge_options'] = unique_badges

        return context

class BizWorkerReviewSubmitView(BusinessLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import json
        from business.models import WorkerReview # Import added

        try:
            data = json.loads(request.body)
            app_id = data.get('app_id')
            review_type = data.get('review_type')
            skills = data.get('skills', [])
            message = data.get('message', '')
            group_ids = data.get('group_ids', [])
            
            store_id = self.kwargs['store_id']
            
            # Verify Application
            app = JobApplication.objects.get(id=app_id)
            if app.job_posting.template.store.id != store_id:
                return JsonResponse({'status': 'error', 'message': 'Invalid store'}, status=403)
            
            # Check for existing review (Idempotency)
            if WorkerReview.objects.filter(job_application=app).exists():
                return JsonResponse({'status': 'success', 'message': 'Already reviewed'})

            # Create Review
            review = WorkerReview.objects.create(
                job_application=app,
                store_id=store_id,
                worker=app.worker,
                review_type=review_type,
                skills=skills,
                message=message
            )
            
            # Add to groups based on skills
            from accounts.models import Badge, WorkerBadge

            for skill_name in skills:
                # 1. Update Badge counts
                badge = Badge.objects.filter(name=skill_name).first()
                if badge:
                    worker_profile = app.worker.workerprofile
                    wb, _ = WorkerBadge.objects.get_or_create(worker=worker_profile, badge=badge)
                    
                    # Increment certified count (always)
                    wb.certified_count += 1
                    
                    # Increment certified store count (if this store hasn't awarded this badge before)
                    # Check past reviews from this store for this worker that included this skill
                    # Note: skills is JSONField, filtered by containment or exact match depends on DB
                    # Here we check Python side or simple query ideally. 
                    # JSONField 'contains' lookup works for lists in some DBs, assuming filtering works:
                    has_awarded_before = WorkerReview.objects.filter(
                        worker=app.worker, 
                        store_id=store_id
                    ).exclude(id=review.id).filter(skills__icontains=skill_name).exists()
                    
                    if not has_awarded_before:
                         wb.certified_store_count += 1
                    
                    wb.is_obtained = True
                    wb.save()

                # 2. Add to StoreWorkerGroup (Existing logic)
                group_def, _ = StoreGroupDefinition.objects.get_or_create(
                    store_id=store_id,
                    name=skill_name,
                    defaults={'is_shared': False, 'is_system': False}
                )
                StoreWorkerGroup.objects.get_or_create(
                    store_id=store_id,
                    worker=app.worker.workerprofile,
                    group_definition=group_def
                )

            # Add to explicitly selected groups
            for g_id in group_ids:
                try:
                    g_def = StoreGroupDefinition.objects.get(id=g_id, store_id=store_id)
                    StoreWorkerGroup.objects.get_or_create(
                        store_id=store_id,
                        worker=app.worker.workerprofile,
                        group_definition=g_def
                    )
                except StoreGroupDefinition.DoesNotExist:
                    continue
            
            # 報酬支払い処理
            if not app.is_reward_paid:
                reward_amount = app.get_calculated_reward()
                if reward_amount > 0:
                    WalletTransaction.objects.create(
                        worker=app.worker.workerprofile,
                        amount=reward_amount,
                        transaction_type='reward',
                        description=f"{app.job_posting.template.store.store_name} 報酬"
                    )
                    app.is_reward_paid = True
                    app.status = '完了'
                    app.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class BizInquiryCompleteView(BusinessLoginRequiredMixin, TemplateView):
    """事業者用お問い合わせ完了（自動返信表示）"""
    template_name = 'business/Support/inquiry_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs.get('store_id')
        biz_profile = BusinessProfile.objects.filter(user=self.request.user).first()
        context['store'] = get_object_or_404(Store, id=store_id, business=biz_profile)
        return context

class BizAccountInfoView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Account/info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        context['biz_profile'] = biz_profile
        return context

class BizBasicInfoEditView(BusinessLoginRequiredMixin, FormView):
    template_name = 'business/Account/basic_info_edit.html'
    form_class = BizBasicInfoForm
    success_url = reverse_lazy('biz_account_info')

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        biz_profile = get_object_or_404(BusinessProfile, user=user)
        initial['last_name'] = user.last_name
        initial['first_name'] = user.first_name
        initial['phone_number'] = biz_profile.phone_number
        initial['email'] = user.email
        return initial

    def form_valid(self, form):
        user = self.request.user
        biz_profile = get_object_or_404(BusinessProfile, user=user)
        
        # User情報の更新
        user.last_name = form.cleaned_data['last_name']
        user.first_name = form.cleaned_data['first_name']
        
        email = form.cleaned_data['email']
        user.email = email
        user.username = email # usernameも合わせる
        
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        
        # パスワード変更後にセッションが切れないようにする
        if password:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, user)
        
        # BusinessProfile情報の更新
        biz_profile.phone_number = form.cleaned_data['phone_number']
        biz_profile.save()
        
        messages.success(self.request, "アカウント情報の更新を行いました。")
        return super().form_valid(form)

class BizReviewCompleteView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/Workers/review_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # サイドバー表示用
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        context['store'] = store
        return context


class BizMessageListView(BusinessLoginRequiredMixin, ListView):
    """メッセージ一覧 (チャットルーム一覧)"""
    model = ChatRoom
    template_name = 'business/Messages/message_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)

        queryset = ChatRoom.objects.filter(
            store=self.store
        ).select_related('worker', 'store').prefetch_related('messages')

        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            queryset = queryset.filter(Q(worker__last_name__icontains=q) | Q(worker__first_name__icontains=q))
        
        queryset = queryset.order_by('-updated_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class BizMessageDetailView(BusinessLoginRequiredMixin, TemplateView):
    """メッセージ詳細 (チャット画面)"""
    template_name = 'business/Messages/message_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs['room_id']
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        
        self.room = get_object_or_404(
            ChatRoom, 
            id=room_id, 
            store__business=biz_profile
        )
        
        context['room'] = self.room
        context['chat_messages'] = self.room.messages.all().select_related('sender')
        context['store'] = self.room.store
        context['application'] = None # 互換性のためNoneまたは最新のApplicationを取得してもよい
        return context

    def post(self, request, *args, **kwargs):
        room_id = self.kwargs['room_id']
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        
        room = get_object_or_404(
            ChatRoom, 
            id=room_id, 
            store__business=biz_profile
        )
        
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                is_read=False
            )
            # Roomの更新日時を更新
            room.updated_at = timezone.now()
            room.save()
        
        return redirect('biz_message_detail', room_id=room_id)

class BizCheckinManagementView(BusinessLoginRequiredMixin, TemplateView):
    """チェックイン/アウト管理 (QRコード表示)"""
    template_name = 'business/Workers/checkin_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # サイドバー表示用
        store_id = self.kwargs.get('store_id')
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        context['store'] = get_object_or_404(Store, id=store_id, business=biz_profile)
        return context

# -----------------------------
# 勤怠修正依頼 (店舗側)
# -----------------------------

class AttendanceCorrectionListView(BusinessLoginRequiredMixin, ListView):
    model = AttendanceCorrection
    template_name = 'business/Workers/attendance_correction_list.html'
    context_object_name = 'corrections'

    def get_queryset(self):
        store_id = self.kwargs['store_id']
        store = get_object_or_404(Store, id=store_id, business__user=self.request.user)
        # 該当店舗の求人への応募に関連する修正依頼を取得
        return AttendanceCorrection.objects.filter(
            application__job_posting__template__store=store
        ).exclude(status='rejected').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs['store_id']
        context['store'] = get_object_or_404(Store, id=store_id, business__user=self.request.user)
        return context

class AttendanceCorrectionDetailView(BusinessLoginRequiredMixin, DetailView):
    model = AttendanceCorrection
    template_name = 'business/Workers/attendance_correction_detail.html'
    context_object_name = 'correction'

    def get_queryset(self):
        store_id = self.kwargs['store_id']
        store = get_object_or_404(Store, id=store_id, business__user=self.request.user)
        return AttendanceCorrection.objects.filter(
            application__job_posting__template__store=store
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs['store_id']
        context['store'] = get_object_or_404(Store, id=store_id, business__user=self.request.user)
        
        # 差分計算などのロジックをViewで渡すか、テンプレートで計算するか
        # ここではシンプルにそのまま渡す
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action') 
        store_id = self.kwargs['store_id']

        if action == 'approve':
            self.object.status = 'approved'
            self.object.save()
            
            # JobApplicationの情報を更新
            application = self.object.application
            application.attendance_at = self.object.correction_attendance_at
            application.leaving_at = self.object.correction_leaving_at
            application.actual_break_duration = self.object.correction_break_time
            
            # 報酬確定・ウォレット追加
            application.status = '完了'
            reward_amount = application.get_calculated_reward()
            application.is_reward_paid = True
            application.save() # status, times, is_reward_paid
            
            from accounts.models import WalletTransaction
            WalletTransaction.objects.create(
                worker=application.worker.workerprofile,
                amount=reward_amount,
                transaction_type='reward',
                description=f"{application.job_posting.template.store.store_name} 報酬 (修正承認)"
            )
            
            # 実績(EXP)の加算
            from accounts.services import AchievementService
            
            # 労働時間計算
            if application.attendance_at and application.leaving_at:
                 duration_seconds = (application.leaving_at - application.attendance_at).total_seconds()
                 total_minutes = int(duration_seconds / 60)
                 
                 # 休憩時間は労働時間を超えないように制限
                 break_minutes_raw = application.actual_break_duration 
                 break_minutes = min(break_minutes_raw, total_minutes)
                 
                 work_minutes = max(0, total_minutes - break_minutes)
            else:
                 work_minutes = 0
            
            earned_exp = AchievementService.calculate_exp_from_minutes(work_minutes)
            AchievementService.add_exp(application.worker.workerprofile, earned_exp, "業務完了(修正承認)")
            
            messages.success(request, '勤怠修正を承認しました。')
            
        elif action == 'reject':
            self.object.status = 'rejected'
            self.object.reject_reason = request.POST.get('reject_reason', '') # 理由を保存
            self.object.save()
            messages.success(request, '修正依頼の拒否をワーカーに送信しました。')

        return redirect('biz_attendance_correction_list', store_id=store_id)


class AnnualLimitReleaseWorkerListView(BusinessLoginRequiredMixin, ListView):
    """年間報酬による制限の解除 - ワーカー選択画面"""
    template_name = 'business/Limit/limit_release_worker_list.html'
    context_object_name = 'workers'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # この店舗に関連するワーカー（Worked or Grouped）
        past_worker_ids = JobApplication.objects.filter(
            job_posting__template__store=self.store
        ).values_list('worker_id', flat=True)
        group_worker_ids = StoreWorkerGroup.objects.filter(
            store=self.store
        ).values_list('worker_id', flat=True)
        all_worker_ids = set(list(past_worker_ids) + list(group_worker_ids))
        
        return User.objects.filter(id__in=all_worker_ids, businessprofile__isnull=True).select_related('workerprofile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class AnnualLimitReleaseView(BusinessLoginRequiredMixin, TemplateView):
    """年間報酬による制限の解除 - 説明画面"""
    template_name = 'business/Limit/annual_limit_release.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs.get('store_id')
        worker_id = self.kwargs.get('worker_id')
        store = get_object_or_404(Store, id=store_id)
        worker = get_object_or_404(WorkerProfile, id=worker_id)
        context['store'] = store
        context['worker'] = worker
        return context

class AnnualLimitReleaseConfirmView(BusinessLoginRequiredMixin, TemplateView):
    """年間報酬による制限の解除 - 確認画面"""
    template_name = 'business/Limit/annual_limit_release_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs.get('store_id')
        worker_id = self.kwargs.get('worker_id')
        store = get_object_or_404(Store, id=store_id)
        worker = get_object_or_404(WorkerProfile, id=worker_id)
        context['store'] = store
        context['worker'] = worker
        return context
    
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

class AnnualLimitReleaseFinishView(BusinessLoginRequiredMixin, TemplateView):
    """年間報酬による制限の解除 - 完了画面"""
    template_name = 'business/Limit/annual_limit_release_finish.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs.get('store_id')
        worker_id = self.kwargs.get('worker_id')
        store = get_object_or_404(Store, id=store_id)
        worker = get_object_or_404(WorkerProfile, id=worker_id)
        context['store'] = store
        context['worker'] = worker
        return context
        
    def post(self, request, *args, **kwargs):
        store_id = self.kwargs.get('store_id')
        worker_id = self.kwargs.get('worker_id')
        store = get_object_or_404(Store, id=store_id)
        worker = get_object_or_404(WorkerProfile, id=worker_id)
        
        # 依頼レコードの作成（重複チェックは簡易的に行う）
        obj, created = AnnualLimitReleaseRequest.objects.get_or_create(
            store=store,
            worker=worker,
            status='pending'
        )
        return self.get(request, *args, **kwargs)



class StoreReviewListView(BusinessLoginRequiredMixin, ListView):
    model = StoreReview
    template_name = 'business/Store/store_reviews.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        # 店舗に紐づくレビューを取得 (新しい順)
        store_id = self.kwargs.get('store_id')
        get_object_or_404(Store, id=store_id, business__user=self.request.user)
        return StoreReview.objects.filter(store_id=store_id).select_related('worker').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = context['reviews']
        store_id = self.kwargs.get('store_id')
        context['store'] = Store.objects.get(id=store_id)
        
        # 統計データの計算
        total_reviews = reviews.count()
        if total_reviews > 0:
            # 各項目のGood数
            time_good = sum(1 for r in reviews if r.is_time_matched)
            content_good = sum(1 for r in reviews if r.is_content_matched)
            again_good = sum(1 for r in reviews if r.is_want_to_work_again)
            
            # 各項目の計算
            context['time_stats'] = {
                'good': time_good,
                'bad': total_reviews - time_good,
                'rate': int((time_good / total_reviews) * 100)
            }
            context['content_stats'] = {
                'good': content_good,
                'bad': total_reviews - content_good,
                'rate': int((content_good / total_reviews) * 100)
            }
            context['again_stats'] = {
                'good': again_good,
                'bad': total_reviews - again_good,
                'rate': int((again_good / total_reviews) * 100)
            }
            
            # 総合Good率 (全項目のGood総数 / (レビュー数 * 3))
            total_items = total_reviews * 3
            total_good = time_good + content_good + again_good
            context['overall_good_rate'] = int((total_good / total_items) * 100)
            
        else:
            # レビューがない場合
            empty_stats = {'good': 0, 'bad': 0, 'rate': 0}
            context['time_stats'] = empty_stats
            context['content_stats'] = empty_stats
            context['again_stats'] = empty_stats
            context['overall_good_rate'] = 0
            
        return context

class DebugSetupReviewView(View):
    def get(self, request):
        from django.http import HttpResponse
        from business.models import Store, JobTemplate, JobPosting, JobApplication
        from django.contrib.auth.models import User
        import datetime
        
        # 1. Store: 海浜幕張カフェ
        store_name = "海浜幕張カフェ"
        store, created = Store.objects.get_or_create(
            store_name=store_name,
            defaults={
                'industry': '飲食・フード',
                'post_code': '261-0021',
                'prefecture': '千葉県',
                'city': '千葉市美浜区',
                'address_line': 'ひび野2-110',
                'building': 'ペリエ海浜幕張',
            }
        )
        if store.industry != '飲食・フード':
             store.industry = '飲食・フード'
             store.save()

        # 2. Worker
        worker = User.objects.filter(is_superuser=False, is_staff=False).first()
        if not worker:
            worker = User.objects.create_user('debug_worker', 'debug@example.com', 'password123')
            worker.last_name = "山田"
            worker.first_name = "太郎"
            worker.save()

        # 3. JobTemplate
        template, _ = JobTemplate.objects.get_or_create(
            store=store,
            title="デバッグ用ホールスタッフ募集",
            defaults={
                'hourly_wage': 1200,
                'transportation_fee': 500,
                'work_content': "ホール業務全般、接客、配膳など",
                'min_age': 18,
                'max_age': 60,
            }
        )

        # 4. JobPosting
        today = timezone.now().date()
        posting, _ = JobPosting.objects.get_or_create(
            template=template,
            work_date=today,
            defaults={ # When creating if not exists
                'title': "【急募】ランチタイムホールスタッフ",
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(15, 0),
                'hourly_wage': 1200,
                'transportation_fee': 500,
                'recruitment_count': 1,
                'work_content': "ホール業務全般"
            }
        )
        
        # 既存の場合も日付等は更新しないが、Applicationの準備へ

        # 5. JobApplication
        app, _ = JobApplication.objects.get_or_create(
            job_posting=posting,
            worker=worker,
            defaults={'status': '確定済み'}
        )
        
        # Simulate Check-in/out if empty
        if not app.attendance_at:
            app.attendance_at = timezone.now() - datetime.timedelta(hours=5)
        if not app.leaving_at:
            app.leaving_at = timezone.now() - datetime.timedelta(minutes=10)
        
        app.status = '確定済み' # Ensure status
        app.save()

        # Review URL
        review_url = reverse('biz_worker_review_list', kwargs={'store_id': store.id, 'job_id': posting.id})
        
        return HttpResponse(f"""
            <html><body style="padding:40px; font-family:sans-serif;">
            <h1 style="color:#007AFF;">デバッグデータ作成完了</h1>
            <div style="background:#f0f0f0; padding:20px; border-radius:8px;">
                <p><strong>店舗:</strong> {store.store_name} ({store.industry})</p>
                <p><strong>ワーカー:</strong> {worker.last_name} {worker.first_name}</p>
                <p><strong>求人:</strong> {posting.title}</p>
                <p><strong>状態:</strong> 勤務終了（退勤記録あり）</p>
            </div>
            <p style="margin-top:20px;">
                <a href="{review_url}" style="background:#007AFF; color:white; padding:15px 30px; text-decoration:none; border-radius:6px; font-weight:bold;">
                    レビュー画面へ移動する
                </a>
            </p>
            </body></html>
        """)

class BizInquiryView(BusinessLoginRequiredMixin, TemplateView):
    """事業者用お問い合わせフォーム"""
    template_name = 'business/Support/inquiry_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_id = self.kwargs.get('store_id')
        biz_profile = BusinessProfile.objects.filter(user=self.request.user).first()
        context['store'] = get_object_or_404(Store, id=store_id, business=biz_profile)
        return context

    def post(self, request, *args, **kwargs):
        # ここでメール送信処理などを行う（今回はモックなので何もしない）
        store_id = self.kwargs.get('store_id')
        # ユーザーに自動返信テンプレートを表示するために完了画面へ
        return redirect('biz_inquiry_complete', store_id=store_id)

# BizInquiryCompleteView は上部で定義済みのため削除

class BizLogoutView(BusinessLoginRequiredMixin, View):
    """事業者用ログアウト確認 & 実行"""
    template_name = 'business/Auth/logout_confirm.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        return redirect('biz_login')
