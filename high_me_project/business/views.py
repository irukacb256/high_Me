from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from datetime import datetime, date, timedelta

from .models import (
    BusinessProfile, Store, JobTemplate, JobPosting, JobApplication,
    JobTemplatePhoto, QualificationMaster, StoreWorkerGroup, StoreWorkerMemo
)
from accounts.models import WorkerProfile, WorkerBadge # 必要に応じて

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
        # signup_data = request.session.get('biz_signup_data')
        # if not signup_data: return redirect('biz_signup') 
        # 既存コードでもpassしていたので厳密にはチェックしないが、データがないと死ぬ
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
    
    def get_success_url(self):
        return reverse('biz_portal')

class BizPasswordResetView(TemplateView):
    template_name = 'business/password_reset.html'
    def post(self, request):
        return redirect('biz_login')

# --- 業務画面 ---

class BizPortalView(LoginRequiredMixin, TemplateView):
    template_name = 'business/portal.html'

    def get(self, request, *args, **kwargs):
        try:
            biz_profile = BusinessProfile.objects.get(user=request.user)
        except BusinessProfile.DoesNotExist:
            return redirect('biz_business_register')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        biz_profile = BusinessProfile.objects.get(user=self.request.user)
        context['biz_profile'] = biz_profile
        context['stores'] = Store.objects.filter(business=biz_profile)
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
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

class AddStoreView(LoginRequiredMixin, CreateView):
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

class TemplateListView(LoginRequiredMixin, ListView):
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

class TemplateCreateView(LoginRequiredMixin, CreateView):
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

class TemplateDetailView(LoginRequiredMixin, DetailView):
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

class TemplateUpdateView(LoginRequiredMixin, UpdateView):
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

class TemplateDeleteView(LoginRequiredMixin, DeleteView):
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

class JobCreateFromTemplateView(LoginRequiredMixin, FormView):
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

class JobConfirmView(LoginRequiredMixin, TemplateView):
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

class JobPostingListView(LoginRequiredMixin, ListView):
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

class JobPostingDetailView(LoginRequiredMixin, DetailView):
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

class JobWorkerListView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'business/job_worker_list.html'
    context_object_name = 'matched_workers'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        self.store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        self.posting = get_object_or_404(JobPosting, pk=self.kwargs['pk'], template__store=self.store)
        return JobApplication.objects.filter(job_posting=self.posting).select_related('worker', 'worker__workerprofile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 年齢計算ロジック
        today = timezone.now().date()
        applications = context['matched_workers']
        for app in applications:
            profile = getattr(app.worker, 'workerprofile', None)
            if profile and profile.birth_date:
                age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
                app.worker_age = age
            else:
                app.worker_age = "不明"
        
        context['store'] = self.store
        context['posting'] = self.posting
        return context

class JobWorkerDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'business/worker_detail.html'
    context_object_name = 'worker'
    pk_url_kwarg = 'worker_id'

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

class JobPostingVisibilityEditView(LoginRequiredMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingVisibilityForm
    template_name = 'business/job_posting_visibility_edit.html'

    def get_queryset(self):
        biz_profile = get_object_or_404(BusinessProfile, user=self.request.user)
        store = get_object_or_404(Store, id=self.kwargs['store_id'], business=biz_profile)
        return JobPosting.objects.filter(template__store=store)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.object.template.store
        return context

    def get_success_url(self):
        messages.success(self.request, '公開設定を変更しました。')
        return reverse('biz_job_posting_detail', kwargs={'store_id': self.object.template.store.id, 'pk': self.object.id})