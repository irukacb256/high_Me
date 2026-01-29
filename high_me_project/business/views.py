from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
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
    Message, ChatRoom, AttendanceCorrection
)
from accounts.models import WorkerProfile, WorkerBadge # 必要に応じて
from .mixins import BusinessLoginRequiredMixin

from .forms import (
    SignupForm, AccountRegisterForm, BusinessRegisterForm, StoreSetupForm,
    JobTemplateForm, JobCreateFromTemplateForm, JobPostingVisibilityForm
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

# --- 登録フロー ---

class LandingView(TemplateView):
    template_name = 'business/landing.html'

class SignupView(FormView):
    template_name = 'business/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('biz_account_register')

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
    template_name = 'business/account_register.html'
    form_class = AccountRegisterForm
    success_url = reverse_lazy('biz_business_register')

    def dispatch(self, request, *args, **kwargs):
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
    template_name = 'business/business_register.html'
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

class VerifyDocsView(TemplateView):
    template_name = 'business/verify_docs.html'
    
    def post(self, request, *args, **kwargs):
        return redirect('biz_store_setup')

class StoreSetupView(FormView):
    template_name = 'business/store_setup.html'
    form_class = StoreSetupForm
    success_url = reverse_lazy('biz_signup_complete')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'businessprofile'):
                return redirect('biz_portal')
            return super(FormView, self).dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

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

class SignupCompleteView(TemplateView):
    template_name = 'business/signup_complete.html'

class BizLoginView(LoginView):
    template_name = 'business/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # ログイン済みでも強制リダイレクトせず、ログイン画面を表示して別アカウントへの切り替えを許可する
        # (ただし、プロファイルがない場合に登録画面へ勝手に飛ばすのは防ぐ)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('biz_portal')

class BizPasswordResetView(TemplateView):
    template_name = 'business/password_reset.html'
    def post(self, request):
        return redirect('biz_login')

# --- 業務画面 ---

class BizPortalView(BusinessLoginRequiredMixin, TemplateView):
    template_name = 'business/portal.html'

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
    template_name = 'business/dashboard.html'

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
        })
        return context

class AddStoreView(BusinessLoginRequiredMixin, FormView):
    # StoreSetupForm を再利用できるが、BusinessProfileとの紐付けが必要
    template_name = 'business/store_setup.html'
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
    template_name = 'business/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        return JobTemplate.objects.filter(store=self.store).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class TemplateCreateView(BusinessLoginRequiredMixin, CreateView):
    model = JobTemplate
    form_class = JobTemplateForm
    template_name = 'business/template_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        context['store'] = self.store
        context['qualifications'] = QualificationMaster.objects.all().order_by('category', 'name')
        return context

    def form_valid(self, form):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        template = form.save(commit=False)
        template.store = store
        
        # マニュアル処理 (skills, other_conditions)
        template.skills = ",".join(self.request.POST.getlist('skills'))
        template.other_conditions = "\n".join([c for c in self.request.POST.getlist('other_conditions') if c.strip()])
        
        # 待遇のチェックボックス処理 (FormでBooleanとして定義していない場合、またはModelFormで拾えていない場合)
        # JobTemplateFormで fields exclude しているので、ModelFormが自動でやってくれない部分は手動
        # しかし、has_xxx は exclude していないので ModelForm が処理してくれるはず。
        # ただし、CheckboxInput はチェックされていないとPOSTされないので、Falseになる。
        # ModelFormならそれでOK。
        
        # Checkboxes for attributes handled by ModelForm:
        # has_unexperienced_welcome, etc. are NOT excluded, so they should be fine.

        template.save()

        # Photos
        photos = self.request.FILES.getlist('photos')
        for i, photo in enumerate(photos):
            JobTemplatePhoto.objects.create(template=template, image=photo, order=i)

        return redirect('biz_template_list', store_id=store.id)

class TemplateDetailView(BusinessLoginRequiredMixin, DetailView):
    model = JobTemplate
    template_name = 'business/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = Store.objects.filter(business=biz_profile).first() # 簡易的
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
    template_name = 'business/template_form.html'

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
        template.save()

        if 'photos' in self.request.FILES:
            template.photos.all().delete()
            photos = self.request.FILES.getlist('photos')
            for i, photo in enumerate(photos):
                JobTemplatePhoto.objects.create(template=template, image=photo, order=i)

        return redirect('biz_template_list', store_id=template.store.id)

class TemplateDeleteView(BusinessLoginRequiredMixin, DeleteView):
    model = JobTemplate
    template_name = 'business/template_delete_confirm.html'
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
    template_name = 'business/job_create_form.html'
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
    template_name = 'business/job_confirm.html'

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
            return render(request, 'business/job_confirm.html', {
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
    template_name = 'business/job_posting_list.html'
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
        return context

class JobPostingDetailView(BusinessLoginRequiredMixin, DetailView):
    model = JobPosting
    template_name = 'business/job_posting_detail.html'
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
    template_name = 'business/job_worker_list.html'
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
        return context

class JobWorkerDetailView(BusinessLoginRequiredMixin, DetailView):
    model = User
    template_name = 'business/worker_detail.html'
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

        # バッジ取得 (直近の実装に合わせて調整)
        if context['profile']:
            from accounts.models import WorkerBadge
            worker_badges = WorkerBadge.objects.filter(worker=profile).select_related('badge')
            context['badges'] = [wb.badge for wb in worker_badges]
        else:
            context['badges'] = []
            
        context['store'] = self.store
        
        # この店舗でのこのワーカーのメモを取得
        from .models import StoreWorkerMemo, StoreWorkerGroup
        try:
             memo = StoreWorkerMemo.objects.get(store=self.store, worker=context['profile'])
             context['memo'] = memo.memo
        except (StoreWorkerMemo.DoesNotExist, AttributeError):
             context['memo'] = ""

        # グループ分け
        try:
            group = StoreWorkerGroup.objects.get(store=self.store, worker=context['profile'])
            context['group_type'] = group.group_type
        except (StoreWorkerGroup.DoesNotExist, AttributeError):
            context['group_type'] = ""

        return context
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        worker_badges = WorkerBadge.objects.filter(worker=self.object.workerprofile).select_related('badge')
        groups = StoreWorkerGroup.objects.filter(store=store, worker=self.object.workerprofile)
        memo = StoreWorkerMemo.objects.filter(store=store, worker=self.object.workerprofile).first()

        context['store'] = store
        context['worker_badges'] = worker_badges
        context['groups'] = groups
        context['memo'] = memo
        return context

class JobPostingVisibilityEditView(BusinessLoginRequiredMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingVisibilityForm
    template_name = 'business/job_posting_visibility_edit.html'

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
    template_name = 'business/worker_management.html'
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
        
        # Userクエリセット作成
        queryset = User.objects.filter(id__in=all_worker_ids).select_related('workerprofile').order_by('id')

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
        
class BizGroupManagementView(BusinessLoginRequiredMixin, ListView):
    template_name = 'business/group_management.html'
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
    template_name = 'business/worker_review_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        
        # 終了済み求人の応募で、まだレビューがないもの
        from django.utils import timezone
        now = timezone.now()
        
        queryset = JobApplication.objects.filter(
            job_posting__template__store=self.store,
            job_posting__end_time__lt=now,
            worker_review__isnull=True
        ).select_related('worker__workerprofile', 'job_posting')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

class BizWorkerReviewSubmitView(BusinessLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import json
        try:
            data = json.loads(request.body)
            app_id = data.get('app_id')
            review_type = data.get('review_type')
            skills = data.get('skills', [])
            message = data.get('message', '')
            
            store_id = self.kwargs['store_id']
            
            # Verify Application
            app = JobApplication.objects.get(id=app_id)
            if app.job_posting.template.store.id != store_id:
                return JsonResponse({'status': 'error', 'message': 'Invalid store'}, status=403)
            
            # Create Review
            WorkerReview.objects.create(
                job_application=app,
                store_id=store_id,
                worker=app.worker,
                review_type=review_type,
                skills=skills,
                message=message
            )
            
            # Add to groups based on skills
            for skill_name in skills:
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
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class BizMessageListView(BusinessLoginRequiredMixin, ListView):
    """メッセージ一覧 (チャットルーム一覧)"""
    model = ChatRoom
    template_name = 'business/message_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        # 自分のビジネスに紐づく店舗のチャットルームを取得
        queryset = ChatRoom.objects.filter(
            store__business=biz_profile
        ).select_related('worker', 'store').prefetch_related('messages')

        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            queryset = queryset.filter(Q(worker__last_name__icontains=q) | Q(worker__first_name__icontains=q))
        
        # 最新メッセージ順などでソートしたい場合はここで処理
        # 単純に更新順(updated_at)でソート
        queryset = queryset.order_by('-updated_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        context['store'] = Store.objects.filter(business=biz_profile).first()
        return context

class BizMessageDetailView(BusinessLoginRequiredMixin, TemplateView):
    """メッセージ詳細 (チャット画面)"""
    template_name = 'business/message_detail.html'

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
        context['messages'] = self.room.messages.all().select_related('sender')
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
    template_name = 'business/checkin_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # サイドバー表示用
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = Store.objects.filter(business=biz_profile).first()
        context['store'] = store
        return context

# -----------------------------
# 勤怠修正依頼 (店舗側)
# -----------------------------

class AttendanceCorrectionListView(BusinessLoginRequiredMixin, ListView):
    model = AttendanceCorrection
    template_name = 'business/attendance_correction_list.html'
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
    template_name = 'business/attendance_correction_detail.html'
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
            # 休憩時間はJobApplicationにはないが、JobPostingのを参照しているので、本来は実績として持つべきかもしれない
            # ここでは要件に従い、出勤・退勤日時を更新する
            application.save()
            
            messages.success(request, '勤怠修正を承認しました。')
            
        elif action == 'reject':
            self.object.status = 'rejected'
            self.object.save()
            messages.warning(request, '勤怠修正を却下しました。')

        return redirect('biz_attendance_correction_list', store_id=store_id)

