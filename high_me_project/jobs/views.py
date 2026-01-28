from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, View, FormView
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse_lazy

from business.models import JobPosting, JobApplication, Store
from .models import FavoriteJob, FavoriteStore
from .constants import PREFECTURES, OCCUPATIONS, REWARDS
# 循環参照回避のため、メソッド内でインポートするか、必要なモデルだけトップレベルで
# from accounts.models import WorkerProfile, Badge, WorkerBadge は必要に応じて

from .forms import PrefectureForm

# --- メイン：さがす画面 ---
class IndexView(ListView):
    model = JobPosting
    template_name = 'jobs/index.html'
    context_object_name = 'main_jobs'

    def get_queryset(self):
        self.today = timezone.localdate()
        date_str = self.request.GET.get('date', self.today.strftime('%Y-%m-%d'))
        try:
            self.selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            self.selected_date = self.today

        self.selected_prefs = self.request.GET.getlist('pref')
        # 空文字を除去
        self.selected_prefs = [p for p in self.selected_prefs if p]

        # ユーザーがログインしていて、かつGETパラメータがない場合は、登録情報をデフォルトにする
        if self.request.user.is_authenticated and not self.selected_prefs and not self.request.GET.get('date'):
            if hasattr(self.request.user, 'workerprofile') and self.request.user.workerprofile.target_prefectures:
                saved_prefs = self.request.user.workerprofile.target_prefectures.split(',')
                self.selected_prefs = [p for p in saved_prefs if p]
        
        # カンマ区切りの文字列が含まれている場合、展開する (テンプレート側で join:"," しているため)
        flat_prefs = []
        for p in self.selected_prefs:
            if ',' in p:
                flat_prefs.extend(p.split(','))
            else:
                flat_prefs.append(p)
        self.selected_prefs = flat_prefs

        queryset = JobPosting.objects.filter(is_published=True, work_date=self.selected_date).prefetch_related('template__photos')
        
        if self.selected_prefs:
            queryset = queryset.filter(template__store__prefecture__in=self.selected_prefs)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # お気に入り状況取得
        user_fav_job_ids = []
        if self.request.user.is_authenticated:
            user_fav_job_ids = FavoriteJob.objects.filter(user=self.request.user).values_list('job_posting_id', flat=True)

        context.update({
            'date_list': [self.today + timedelta(days=i) for i in range(14)],
            'selected_date': self.selected_date,
            'selected_prefs': self.selected_prefs,
            'today': self.today,
            'user_fav_job_ids': set(user_fav_job_ids),
        })
        return context

# --- 場所フロー ---
class LocationHomeView(TemplateView):
    template_name = 'jobs/location_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_prefs = []
        # ユーザー設定を取得
        if self.request.user.is_authenticated and hasattr(self.request.user, 'workerprofile'):
            if self.request.user.workerprofile.target_prefectures:
                selected_prefs = [p for p in self.request.user.workerprofile.target_prefectures.split(',') if p]
        
        # GETパラメータがあればそちらを優先
        params = self.request.GET.getlist('pref')
        if params:
            selected_prefs = params
            
        context['selected_prefs'] = selected_prefs
        return context

class PrefSelectView(FormView):
    template_name = 'jobs/pref_select.html'
    form_class = PrefectureForm
    success_url = reverse_lazy('index')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'workerprofile'):
            if self.request.user.workerprofile.target_prefectures:
                initial['pref'] = self.request.user.workerprofile.target_prefectures.split(',')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレート側でループしやすいようにリストも渡す（フォームフィールドのchoicesでもよいが、既存テンプレのデザインに合わせるならリストが必要かも）
        # 既存テンプレートが `prefectures_list` を使っている場合に合わせておく
        context['prefectures_list'] = PREFECTURES
        # 既存テンプレートが `selected_prefs` を使っている
        form = context['form']
        context['selected_prefs'] = form['pref'].value() if form['pref'].value() else []
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'workerprofile'):
            profile = self.request.user.workerprofile
            prefs = form.cleaned_data['pref']
            profile.target_prefectures = ",".join(prefs)
            profile.save()
        return super().form_valid(form)

class MapView(TemplateView):
    template_name = 'jobs/map_view.html'

# --- 絞り込みフロー ---
class RefineHomeView(TemplateView):
    template_name = 'jobs/refine_home.html'

class TimeSelectView(TemplateView):
    template_name = 'jobs/time_select.html'

class TreatmentSelectView(TemplateView):
    template_name = 'jobs/treatment_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['treatment_list'] = ["未経験者歓迎", "バイク/車通勤可", "服装自由", "クーポンGET", "まかないあり", "髪型/カラー自由", "交通費支給"]
        return context

class KeywordExcludeView(TemplateView):
    template_name = 'jobs/keyword_exclude.html'

class OccupationSelectView(TemplateView):
    template_name = 'jobs/occupation_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['occupation_list'] = OCCUPATIONS
        return context

class RewardSelectView(TemplateView):
    template_name = 'jobs/reward_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reward_list'] = REWARDS
        return context


class JobDetailView(DetailView):
    model = JobPosting
    template_name = 'jobs/detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return JobPosting.objects.prefetch_related('template__photos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        is_applied = False
        is_favorited = False
        if self.request.user.is_authenticated:
            is_applied = JobApplication.objects.filter(job_posting=job, worker=self.request.user).exists()
            is_favorited = FavoriteJob.objects.filter(user=self.request.user, job_posting=job).exists()
        
        context['is_applied'] = is_applied
        context['is_favorited'] = is_favorited
        context['is_closed'] = job.is_expired
        return context


class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # お気に入り求人
        favorite_jobs = FavoriteJob.objects.filter(user=self.request.user).select_related('job_posting', 'job_posting__template__store').order_by('-created_at')
        # お気に入り店舗
        favorite_stores = FavoriteStore.objects.filter(user=self.request.user).select_related('store').order_by('-created_at')
        
        context['favorite_jobs'] = favorite_jobs
        context['favorite_stores'] = favorite_stores
        context['tab'] = self.request.GET.get('tab', 'jobs')
        return context


class StoreProfileView(LoginRequiredMixin, DetailView):
    model = Store
    template_name = 'jobs/store_profile.html'
    context_object_name = 'store'
    pk_url_kwarg = 'store_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.object
        
        # この店舗の求人一覧（期限切れでないもの）
        context['job_postings'] = JobPosting.objects.filter(
            template__store=store,
            work_date__gte=timezone.now().date()
        ).order_by('work_date', 'start_time')
        
        # お気に入り済みかどうか
        context['is_favorited'] = FavoriteStore.objects.filter(user=self.request.user, store=store).exists()
        
        # 求人リストにお気に入り情報を付加
        if self.request.user.is_authenticated:
             user_fav_job_ids = FavoriteJob.objects.filter(user=self.request.user).values_list('job_posting_id', flat=True)
             context['user_fav_job_ids'] = set(user_fav_job_ids)
        else:
             context['user_fav_job_ids'] = set()
             
        return context


class ToggleFavoriteJobView(LoginRequiredMixin, View):
    def post(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(JobPosting, id=job_id)
        fav_job, created = FavoriteJob.objects.get_or_create(user=request.user, job_posting=job)
        
        is_favorited = True
        if not created:
            # 既に存在していた場合は削除（トグル動作）
            fav_job.delete()
            is_favorited = False
            
        return JsonResponse({'status': 'success', 'is_favorited': is_favorited})

class ToggleFavoriteStoreView(LoginRequiredMixin, View):
    def post(self, request, store_id, *args, **kwargs):
        store = get_object_or_404(Store, id=store_id)
        fav_store, created = FavoriteStore.objects.get_or_create(user=request.user, store=store)
        
        is_favorited = True
        if not created:
            fav_store.delete()
            is_favorited = False
            
        return JsonResponse({'status': 'success', 'is_favorited': is_favorited})


class WorkScheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/work_schedule.html'

    def group_by_date(self, app_list):
        grouped = {}
        # 曜日変換マップ
        weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        for app in app_list:
            d = app.job_posting.work_date
            if d not in grouped:
                # (曜日(JP), アプリリスト)
                grouped[d] = [weekday_map[d.weekday()], []]
            grouped[d][1].append(app)
        
        # [(date, weekday_jp, [apps]), ...] の形式でソートして返す
        result = []
        for d in sorted(grouped.keys()):
            result.append((d, grouped[d][0], grouped[d][1]))
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # ユーザーの応募済み求人を全て取得（勤務日の昇順）
        applications = JobApplication.objects.filter(worker=self.request.user).select_related('job_posting', 'job_posting__template__store').order_by('job_posting__work_date', 'job_posting__start_time')
        
        upcoming = []
        completed = []
        
        for app in applications:
            # 終了時間を考慮した完了判定
            job_end = timezone.make_aware(datetime.combine(app.job_posting.work_date, app.job_posting.end_time))
            if job_end < now:
                completed.append(app)
            else:
                upcoming.append(app)

        context['upcoming_grouped'] = self.group_by_date(upcoming)
        context['completed_grouped'] = self.group_by_date(completed)
        context['tab'] = self.request.GET.get('tab', 'upcoming')
        return context


class MessagesView(TemplateView):
    template_name = 'jobs/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        has_requests = False # お仕事リクエスト
        
        # 長期バイトの募集があるか
        # is_long_term=True の求人が存在し、かつ掲載中であること
        has_long_term = JobPosting.objects.filter(is_long_term=True, is_published=True, work_date__gte=date.today()).exists()
        
        # マッチング中の仕事があるか
        has_matches = False
        if self.request.user.is_authenticated:
            has_matches = JobApplication.objects.filter(worker=self.request.user, status='確定済み').exists()
        
        show_empty = not (has_requests or has_long_term or has_matches)
        
        context.update({
            'has_requests': has_requests,
            'has_long_term': has_long_term,
            'has_matches': has_matches,
            'show_empty': show_empty
        })
        return context

# --- 申し込みフロー ---

class ApplyStep1BelongingsView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/apply_belongings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def get(self, request, *args, **kwargs):
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        profile = request.user.workerprofile

        # 本人確認をしていない場合
        if not profile.is_identity_verified:
            return render(request, 'jobs/detail.html', {'job': job, 'needs_verification': True})

        # 求人が締切済み/満員の場合
        if job.is_expired:
            return render(request, 'jobs/detail.html', {'job': job, 'is_closed': True})
            
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_2_conditions', pk=self.kwargs['pk'])


class ApplyStep2ConditionsView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/apply_conditions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_3_documents', pk=self.kwargs['pk'])


class ApplyStep3DocumentsView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/apply_documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_4_policy', pk=self.kwargs['pk'])


class ApplyStep4PolicyView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/apply_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_5_review', pk=self.kwargs['pk'])


class ApplyStep5ReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/apply_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        # --- ここで実際の申し込みデータを保存する ---
        JobApplication.objects.get_or_create(
            job_posting=job,
            worker=request.user
        )
        return render(request, 'jobs/apply_complete.html', {'job': job})

class JobWorkingDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/job_working_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=self.request.user)
        
        weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        weekday_jp = weekday_map[application.job_posting.work_date.weekday()]
        
        context['app'] = application
        context['weekday_jp'] = weekday_jp
        return context

class BadgeListView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/badge_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import Badge, WorkerBadge 
        
        badges = Badge.objects.all()
        my_badges = WorkerBadge.objects.filter(worker=self.request.user.workerprofile).select_related('badge')
        my_badges_dict = {wb.badge.id: wb for wb in my_badges}
        
        context['badges'] = badges
        context['my_badges_dict'] = my_badges_dict
        return context
