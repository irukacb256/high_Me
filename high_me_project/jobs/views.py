from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, View, FormView, CreateView
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse_lazy, reverse

from business.models import JobPosting, JobApplication, Store, AttendanceCorrection, ChatRoom, StoreReview
from .models import FavoriteJob, FavoriteStore
from .constants import PREFECTURES, OCCUPATIONS, REWARDS
from accounts.models import Badge
# 循環参照回避のため、メソッド内でインポートするか、必要なモデルだけトップレベルで
# from accounts.models import WorkerProfile, Badge, WorkerBadge は必要に応じて

from .forms import PrefectureForm, StoreReviewStep1Form, StoreReviewStep2Form

# --- メイン：さがす画面 ---
import json
from django.core.serializers.json import DjangoJSONEncoder

class MapSearchView(TemplateView):
    template_name = 'Searchjobs/map_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 対象都道府県
        # 対象都道府県 (GETパラメータがあればそれを使用、なければデフォルト)
        target_prefs = self.request.GET.getlist('pref')
        if not target_prefs:
            target_prefs = ['東京都', '神奈川県', '千葉県']
        
        # 有効な求人で、かつ緯度経度があるもの
        jobs = JobPosting.objects.filter(
            template__store__prefecture__in=target_prefs,
            template__store__latitude__isnull=False,
            template__store__longitude__isnull=False,
            visibility='public'  # 公開中のみ
        ).select_related('template__store')
        
        # マップ表示用データ作成
        map_data = []
        for job in jobs:
            store = job.template.store
            map_data.append({
                'id': job.id,
                'title': job.title,
                'store_name': store.store_name,
                'lat': store.latitude,
                'lng': store.longitude,
                'url': reverse('job_detail', kwargs={'pk': job.id}),
                'salary': f"{job.get_reward_mode_display()}: {job.reward_amount}円",
                'work_date': job.work_date.strftime('%m/%d') if job.work_date else '',
                'time': f"{job.start_time.strftime('%H:%M')}~{job.end_time.strftime('%H:%M')}"
            })
            
        context['map_data_json'] = json.dumps(map_data, cls=DjangoJSONEncoder)
        return context

class IndexView(ListView):
    model = JobPosting
    template_name = 'Searchjobs/index.html'
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

        # セッションから絞り込み条件を取得して適用
        session_filters = self.request.session.get('job_filters', {})
        
        # 職種
        occupations = session_filters.get('occupations', [])
        if occupations:
            queryset = queryset.filter(template__occupation__in=occupations)

        # 報酬
        rewards = session_filters.get('rewards', [])
        if rewards:
            min_wage = 0
            for r in rewards:
                import re
                match = re.search(r'(\d{1,3}(,\d{3})*)', r)
                if match:
                    val = int(match.group(1).replace(',', ''))
                    if min_wage == 0 or val < min_wage:
                        min_wage = val
            if min_wage > 0:
                queryset = queryset.filter(hourly_wage__gte=min_wage)

        # 待遇
        treatments = session_filters.get('treatments', [])
        if treatments:
            treatment_map = {
                "未経験者歓迎": "has_unexperienced_welcome",
                "バイク/車通勤可": "has_bike_car_commute",
                "服装自由": "has_clothing_free",
                "クーポンGET": "has_coupon_get",
                "まかないあり": "has_meal",
                "髪型/カラー自由": "has_hair_color_free",
                "交通費支給": "has_transportation_allowance"
            }
            for t in treatments:
                field_name = treatment_map.get(t)
                if field_name:
                    queryset = queryset.filter(**{f"template__{field_name}": True})

        # 時間帯
        time_ranges = session_filters.get('time_ranges', [])
        if time_ranges:
            time_q = Q()
            for tr in time_ranges:
                if tr == "朝 (4:00〜10:00)":
                    time_q |= Q(start_time__gte="04:00", start_time__lt="10:00")
                elif tr == "昼 (10:00〜16:00)":
                    time_q |= Q(start_time__gte="10:00", start_time__lt="16:00")
                elif tr == "夕方 (16:00〜22:00)":
                    time_q |= Q(start_time__gte="16:00", start_time__lt="22:00")
                elif tr == "深夜 (22:00〜4:00)":
                    time_q |= Q(start_time__gte="22:00") | Q(start_time__lt="04:00")
            queryset = queryset.filter(time_q)

        # 除外キーワード
        exclude_keyword = session_filters.get('exclude_keyword', '')
        if exclude_keyword:
            keywords = exclude_keyword.replace('　', ' ').split()
            for k in keywords:
                if k:
                    queryset = queryset.exclude(title__icontains=k).exclude(template__work_content__icontains=k)
            
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
    template_name = 'Searchjobs/location_home.html'

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
    template_name = 'Searchjobs/pref_select.html'
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

import json
from django.core.serializers.json import DjangoJSONEncoder

class MapView(TemplateView):
    template_name = 'Searchjobs/map_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.localdate()
        date_list = [today + timedelta(days=i) for i in range(14)]
        
        # 対象都道府県 (GETパラメータがあればそれを使用、なければユーザーの登録設定)
        target_prefs = self.request.GET.getlist('pref')
        if not target_prefs and self.request.user.is_authenticated and hasattr(self.request.user, 'workerprofile'):
            if self.request.user.workerprofile.target_prefectures:
                target_prefs = [p for p in self.request.user.workerprofile.target_prefectures.split(',') if p]
        
        if not target_prefs:
            target_prefs = ['東京都', '神奈川県', '千葉県']

        qs = JobPosting.objects.filter(
            visibility='public',
            is_published=True,
            work_date__gte=today, # 今日以降
            work_date__lte=today + timedelta(days=14),
            template__store__prefecture__in=target_prefs,
            template__store__latitude__isnull=False,
            template__store__longitude__isnull=False
        ).select_related('template', 'template__store')

        # セッションから絞り込み条件を取得して適用 (IndexViewと同様のロジック)
        session_filters = self.request.session.get('job_filters', {})
        
        # 職種
        occupations = session_filters.get('occupations', [])
        if occupations:
            qs = qs.filter(template__occupation__in=occupations)

        # 報酬
        rewards = session_filters.get('rewards', [])
        if rewards:
            min_wage = 0
            for r in rewards:
                import re
                match = re.search(r'(\d{1,3}(,\d{3})*)', r)
                if match:
                    val = int(match.group(1).replace(',', ''))
                    if min_wage == 0 or val < min_wage:
                        min_wage = val
            if min_wage > 0:
                qs = qs.filter(hourly_wage__gte=min_wage)

        # 待遇
        treatments = session_filters.get('treatments', [])
        if treatments:
            treatment_map = {
                "未経験者歓迎": "has_unexperienced_welcome",
                "バイク/車通勤可": "has_bike_car_commute",
                "服装自由": "has_clothing_free",
                "クーポンGET": "has_coupon_get",
                "まかないあり": "has_meal",
                "髪型/カラー自由": "has_hair_color_free",
                "交通費支給": "has_transportation_allowance"
            }
            for t in treatments:
                field_name = treatment_map.get(t)
                if field_name:
                    qs = qs.filter(**{f"template__{field_name}": True})

        # 時間帯
        time_ranges = session_filters.get('time_ranges', [])
        if time_ranges:
            time_q = Q()
            for tr in time_ranges:
                if tr == "朝 (4:00〜10:00)":
                    time_q |= Q(start_time__gte="04:00", start_time__lt="10:00")
                elif tr == "昼 (10:00〜16:00)":
                    time_q |= Q(start_time__gte="10:00", start_time__lt="16:00")
                elif tr == "夕方 (16:00〜22:00)":
                    time_q |= Q(start_time__gte="16:00", start_time__lt="22:00")
                elif tr == "深夜 (22:00〜4:00)":
                    time_q |= Q(start_time__gte="22:00") | Q(start_time__lt="04:00")
            qs = qs.filter(time_q)

        # 除外キーワード
        exclude_keyword = session_filters.get('exclude_keyword', '')
        if exclude_keyword:
            keywords = exclude_keyword.replace('　', ' ').split()
            for k in keywords:
                if k:
                    qs = qs.exclude(title__icontains=k).exclude(template__work_content__icontains=k)
        
        jobs_data = []
        for job in qs:
            start_dt = datetime.combine(job.work_date, job.start_time)
            is_expired = timezone.make_aware(start_dt) < timezone.now()
            
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'work_date': job.work_date.strftime('%Y-%m-%d'),
                'start_time': job.start_time.strftime('%H:%M'),
                'end_time': job.end_time.strftime('%H:%M'),
                'lat': float(job.template.store.latitude),
                'lng': float(job.template.store.longitude),
                'store_name': job.template.store.store_name,
                'hourly_wage': int(job.hourly_wage),
                'is_expired': bool(is_expired),
                'recruitment_count': int(job.recruitment_count),
            })
            
        context['jobs_data'] = jobs_data
        context['date_list'] = date_list
        context['today_str'] = today.strftime('%Y-%m-%d')
        return context

# --- 絞り込みフロー ---
class RefineHomeView(TemplateView):
    template_name = 'Searchjobs/refine_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 現在のフィルタ状態を表示用に渡す
        session_filters = self.request.session.get('job_filters', {})
        context['current_occupations'] = session_filters.get('occupations', [])
        context['current_rewards'] = session_filters.get('rewards', [])
        context['current_time_ranges'] = session_filters.get('time_ranges', [])
        context['current_treatments'] = session_filters.get('treatments', [])
        context['current_exclude_keyword'] = session_filters.get('exclude_keyword', '')
        return context

    def post(self, request, *args, **kwargs):
        # "すべて解除" や 個別のリセット用
        if 'reset' in request.POST:
            if 'job_filters' in request.session:
                del request.session['job_filters']
        return redirect('refine_home')

class TimeSelectView(TemplateView):
    template_name = 'Searchjobs/time_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.request.session.get('job_filters', {})
        context['selected_time_ranges'] = filters.get('time_ranges', [])
        context['time_list'] = ["朝 (4:00〜10:00)", "昼 (10:00〜16:00)", "夕方 (16:00〜22:00)", "深夜 (22:00〜4:00)"]
        return context

    def post(self, request, *args, **kwargs):
        selected = request.POST.getlist('time_range')
        filters = request.session.get('job_filters', {})
        filters['time_ranges'] = selected
        request.session['job_filters'] = filters
        return redirect('refine_home')

class TreatmentSelectView(TemplateView):
    template_name = 'Searchjobs/treatment_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['treatment_list'] = ["未経験者歓迎", "バイク/車通勤可", "服装自由", "クーポンGET", "まかないあり", "髪型/カラー自由", "交通費支給"]
        filters = self.request.session.get('job_filters', {})
        context['selected_treatments'] = filters.get('treatments', [])
        return context

    def post(self, request, *args, **kwargs):
        selected = request.POST.getlist('treatment')
        filters = request.session.get('job_filters', {})
        filters['treatments'] = selected
        request.session['job_filters'] = filters
        return redirect('refine_home')

class KeywordExcludeView(TemplateView):
    template_name = 'Searchjobs/keyword_exclude.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.request.session.get('job_filters', {})
        context['exclude_keyword'] = filters.get('exclude_keyword', '')
        return context

    def post(self, request, *args, **kwargs):
        keyword = request.POST.get('keyword', '')
        filters = request.session.get('job_filters', {})
        filters['exclude_keyword'] = keyword
        request.session['job_filters'] = filters
        return redirect('refine_home')

class OccupationSelectView(TemplateView):
    template_name = 'Searchjobs/occupation_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['occupation_list'] = OCCUPATIONS
        filters = self.request.session.get('job_filters', {})
        context['selected_occupations'] = filters.get('occupations', [])
        return context

    def post(self, request, *args, **kwargs):
        selected = request.POST.getlist('occupation')
        filters = request.session.get('job_filters', {})
        filters['occupations'] = selected
        request.session['job_filters'] = filters
        return redirect('refine_home')

class RewardSelectView(TemplateView):
    template_name = 'Searchjobs/reward_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reward_list'] = REWARDS
        filters = self.request.session.get('job_filters', {})
        context['selected_rewards'] = filters.get('rewards', [])
        return context

    def post(self, request, *args, **kwargs):
        selected = request.POST.getlist('reward')
        filters = request.session.get('job_filters', {})
        filters['rewards'] = selected
        request.session['job_filters'] = filters
        return redirect('refine_home')


class JobDetailView(DetailView):
    model = JobPosting
    template_name = 'Searchjobs/detail.html'
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
    template_name = 'Favorites/favorites.html'

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
    template_name = 'Searchjobs/store_profile.html'
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
    template_name = 'Work/work_schedule.html'

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
            # 終了時間を考慮した完了判定 or ステータス完了
            job_end = timezone.make_aware(datetime.combine(app.job_posting.work_date, app.job_posting.end_time))
            if app.status == '完了' or job_end < now:
                completed.append(app)
            else:
                upcoming.append(app)

        context['upcoming_grouped'] = self.group_by_date(upcoming)
        context['completed_grouped'] = self.group_by_date(completed)
        context['tab'] = self.request.GET.get('tab', 'upcoming')
        return context


class MessagesView(TemplateView):
    template_name = 'Messages/messages.html'

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
    template_name = 'Searchjobs/Apply/apply_belongings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def get(self, request, *args, **kwargs):
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        profile = request.user.workerprofile

        # 本人確認をしていない場合
        if not profile.is_identity_verified:
            return render(request, 'Searchjobs/detail.html', {'job': job, 'needs_verification': True})

        # 求人が締切済み/満員の場合
        if job.is_expired:
            return render(request, 'Searchjobs/detail.html', {'job': job, 'is_closed': True})
            
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_2_conditions', pk=self.kwargs['pk'])


class ApplyStep2ConditionsView(LoginRequiredMixin, TemplateView):
    template_name = 'Searchjobs/Apply/apply_conditions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_3_documents', pk=self.kwargs['pk'])


class ApplyStep3DocumentsView(LoginRequiredMixin, TemplateView):
    template_name = 'Searchjobs/Apply/apply_documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_4_policy', pk=self.kwargs['pk'])


class ApplyStep4PolicyView(LoginRequiredMixin, TemplateView):
    template_name = 'Searchjobs/Apply/apply_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        return redirect('apply_step_5_review', pk=self.kwargs['pk'])


class ApplyStep5ReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'Searchjobs/Apply/apply_review.html'

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

        # マッチングした時点でチャットルームを作成する
        # 店舗とワーカーの組み合わせで作成
        store = job.template.store
        ChatRoom.objects.get_or_create(
            store=store,
            worker=request.user
        )

        return render(request, 'Searchjobs/Apply/apply_complete.html', {'job': job})

class JobWorkingDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'Work/job_working_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=self.request.user)
        
        weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        weekday_jp = weekday_map[application.job_posting.work_date.weekday()]
        
        context['app'] = application
        context['weekday_jp'] = weekday_jp
        
        # 質問回答済みかどうか
        context['is_answered'] = application.answered_at is not None
        context['questions_exist'] = any([
            application.job_posting.template.question1,
            application.job_posting.template.question2,
            application.job_posting.template.question3
        ])
        
        # チャットルーム取得 (お問い合わせ用)
        from business.models import ChatRoom
        try:
            room = ChatRoom.objects.get(
                store=application.job_posting.template.store, 
                worker=self.request.user
            )
            context['chat_room'] = room
        except ChatRoom.DoesNotExist:
            context['chat_room'] = None

        return context

class JobAnswerView(LoginRequiredMixin, TemplateView):
    template_name = 'Work/job_answer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=self.request.user)
        context['app'] = application
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=self.request.user)
        
        # 回答を保存
        application.answer1 = request.POST.get('answer1', '')
        application.answer2 = request.POST.get('answer2', '')
        application.answer3 = request.POST.get('answer3', '')
        application.answered_at = timezone.now()
        application.save()
        
        from django.contrib import messages
        messages.success(request, '働き先への回答を送信しました。')
        return redirect('job_working_detail', pk=pk)

class BadgeListView(LoginRequiredMixin, TemplateView):
    template_name = 'MyPage/Badges/badge_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import Badge, WorkerBadge 
        
        badges = Badge.objects.all()
        my_badges = WorkerBadge.objects.filter(worker=self.request.user.workerprofile).select_related('badge')
        my_badges_dict = {wb.badge.id: wb for wb in my_badges}
        
        context['badges'] = badges
        context['my_badges_dict'] = my_badges_dict
        return context

class BadgeDetailView(LoginRequiredMixin, DetailView):
    model = Badge
    template_name = 'MyPage/Badges/badge_detail.html'
    context_object_name = 'badge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 自分の獲得状況を取得
        from accounts.models import WorkerBadge
        try:
            wb = WorkerBadge.objects.get(worker=self.request.user.workerprofile, badge=self.object)
            context['worker_badge'] = wb
            context['is_obtained'] = wb.is_obtained
        except WorkerBadge.DoesNotExist:
            context['worker_badge'] = None
            context['is_obtained'] = False
        return context


class JobQRReaderView(LoginRequiredMixin, TemplateView):
    """QRコード読み取り画面 (カメラシミュレーション)"""
    template_name = 'Work/job_qr_reader.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context


class QRScanView(LoginRequiredMixin, View):
    """QRコード読み取り（シミュレーション）"""
    def post(self, request, pk, *args, **kwargs):
        # pk is job_posting_id
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=request.user)
        
        now = timezone.now()
        is_checkin = False
        
        if not application.attendance_at:
            # チェックイン
            application.attendance_at = now
            application.save()
            is_checkin = True
            return render(request, 'Work/qr_success.html', {
                'app': application, 
                'is_checkin': is_checkin
            })
        elif not application.leaving_at:
            # チェックアウト
            application.leaving_at = now
            application.save()
            is_checkin = False
            # 勤怠修正フローへ
            return redirect('attendance_step1', application_id=application.id)
        else:
            # 既に両方済み
            return redirect('mypage')


# -----------------------------------------------------------------------------
# 勤怠修正フロー (Checkout後)
# -----------------------------------------------------------------------------

class AttendanceStepBaseView(LoginRequiredMixin, View):
    """勤怠修正フローの基底クラス"""
    def get_application(self, application_id):
        # 自分の応募でかつチェックアウト済みのものを取得（チェックアウト直後なのでleaving_atはあるはず）
        return get_object_or_404(JobApplication, id=application_id, worker=self.request.user)

    def get_session_data(self, application_id):
        key = f'correction_data_{application_id}'
        return self.request.session.get(key, {})

    def update_session_data(self, application_id, data):
        key = f'correction_data_{application_id}'
        current_data = self.request.session.get(key, {})
        current_data.update(data)
        self.request.session[key] = current_data
        self.request.session.modified = True

class AttendanceStep1CheckView(AttendanceStepBaseView):
    """Step 1: 就業時間は予定通りでしたか？"""
    template_name = 'Work/attendance_step1.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        
        # 既に修正依頼が存在する場合（却下以外）は申請できないようにする
        if AttendanceCorrection.objects.filter(application=application, status__in=['pending', 'approved']).exists():
            return render(request, 'jobs/attendance_duplicate.html', {'application': application})
            
        return render(request, self.template_name, {'application': application})

    def post(self, request, application_id):
        action = request.POST.get('action')
        if action == 'as_scheduled':
            # 予定通り -> 報酬確認画面へ
            return redirect('reward_confirm', application_id=application_id)
        elif action == 'changed':
            # 変更があった -> Step 2へ
            return redirect('attendance_step2', application_id=application_id)
        return redirect('attendance_step1', application_id=application_id)

class RewardConfirmView(AttendanceStepBaseView):
    """報酬確認画面 (予定通りの場合)"""
    template_name = 'Work/reward_confirm.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        
        # 報酬計算 (予定通りなので募集の開始・終了時間を使用)
        # 実装簡略化のため、今回は単純計算 (休憩時間は募集の規定時間を使用)
        # 本来は深夜割増なども考慮が必要
        
        posting = application.job_posting
        
        # 開始・終了日時 (Date + Time)
        start_dt = datetime.combine(posting.work_date, posting.start_time)
        end_dt = datetime.combine(posting.work_date, posting.end_time)
        
        # 日跨ぎ対応 (終了時間が開始時間より前なら翌日扱い)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
            
        # 総労働時間 (分)
        total_minutes = (end_dt - start_dt).total_seconds() / 60
        
        # 実労働時間 = 総労働時間 - 休憩時間
        work_minutes = total_minutes - posting.break_duration
        if work_minutes < 0:
            work_minutes = 0
            
        # 報酬額 = 時給 * 時間 + 交通費
        wage = posting.hourly_wage
        # 時間計算 (分単位を時間単位に)
        hours = work_minutes / 60
        base_reward = int(wage * hours)
        
        # 交通費 (固定と仮定。本来は交通費支給有無や上限などのロジックがあるはず)
        # 今回は一旦 1000円固定 または postingにフィールドがあればそれを使う
        # posting.transportation_expenses があるか確認していないが、なければ0
        transportation = getattr(posting, 'transportation_expenses_amount', 500) # モデル未確認のためデフォルト仮置き
        if not getattr(posting, 'transportation_expenses', True): # 支給なしなら0
             transportation = 0

        total_amount = base_reward + transportation
        
        context = {
            'application': application,
            'base_reward': base_reward,
            'transportation': transportation,
            'total_amount': total_amount,
            'work_hours': round(hours, 1), # 表示用
        }
        return render(request, self.template_name, context)

    def post(self, request, application_id):
        application = self.get_application(application_id)
        
        # 勤怠情報の確定 (予定通りとして保存)
        # AttendanceCorrectionを作るか、Applicationに直接保存するか
        # ここでは "完了" 状態にする
        # status = 'completed' ? -> モデル定義によるが、とりあえずApplication完了処理
        
        # 予定時間を実績として保存 (念のため上書き、あるいは is_scheduled=True フラグなど)
        application.status = '完了'
        application.save()
        
        # 完了画面ではなく評価入力画面のStep1へ
        return redirect('store_review_step1', application_id=application_id)

class RewardFinishView(AttendanceStepBaseView):
    """報酬確定完了画面"""
    template_name = 'Work/reward_finish.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

class AttendanceStep2GuideView(AttendanceStepBaseView):
    """Step 2: 修正依頼の流れ (ガイド画面)"""
    template_name = 'Work/attendance_step2.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})
        
    def post(self, request, application_id):
        return redirect('attendance_step3', application_id=application_id)

class AttendanceStep3TimeView(AttendanceStepBaseView):
    """Step 3: 業務開始・終了日時の入力"""
    template_name = 'Work/attendance_step3.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        # 初期値は実際の打刻時間、なければ予定時間
        initial = {
            'attendance_date': session_data.get('attendance_date') or (timezone.localtime(application.attendance_at).strftime('%Y-%m-%d') if application.attendance_at else timezone.localtime().strftime('%Y-%m-%d')),
            'attendance_time': session_data.get('attendance_time') or (timezone.localtime(application.attendance_at).strftime('%H:%M') if application.attendance_at else ''),
            'leaving_date': session_data.get('leaving_date') or (timezone.localtime(application.leaving_at).strftime('%Y-%m-%d') if application.leaving_at else timezone.localtime().strftime('%Y-%m-%d')),
            'leaving_time': session_data.get('leaving_time') or (timezone.localtime(application.leaving_at).strftime('%H:%M') if application.leaving_at else ''),
        }
        return render(request, self.template_name, {'application': application, 'initial': initial})

    def post(self, request, application_id):
        # フォームデータの保存
        data = {
            'attendance_date': request.POST.get('attendance_date'),
            'attendance_time': request.POST.get('attendance_time'),
            'leaving_date': request.POST.get('leaving_date'),
            'leaving_time': request.POST.get('leaving_time'),
        }
        self.update_session_data(application_id, data)
        return redirect('attendance_step4', application_id=application_id)

class AttendanceStep4BreakView(AttendanceStepBaseView):
    """Step 4: 休憩時間の入力"""
    template_name = 'Work/attendance_step4.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        initial_break = session_data.get('break_time', application.job_posting.break_duration)
        return render(request, self.template_name, {'application': application, 'break_time': initial_break})

    def post(self, request, application_id):
        break_time = request.POST.get('break_time')
        self.update_session_data(application_id, {'break_time': break_time})
        
        # 遅刻判定
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        # 入力された開始日時を構築
        try:
            att_date = session_data.get('attendance_date')
            att_time = session_data.get('attendance_time')
            input_start_dt = datetime.strptime(f"{att_date} {att_time}", '%Y-%m-%d %H:%M')
            # タイムゾーン考慮が必要であれば make_aware するが、比較元の scheduled_start_dt と合わせる
            input_start_dt = timezone.make_aware(input_start_dt)
            
            # 予定開始日時
            # job_posting.work_date は date型、start_time は time型
            scheduled_start_dt = timezone.make_aware(datetime.combine(application.job_posting.work_date, application.job_posting.start_time))
            
            # 1分以上の遅刻とみなすか
            if input_start_dt > scheduled_start_dt:
                return redirect('attendance_step5', application_id=application_id)
            else:
                return redirect('attendance_step6', application_id=application_id)

        except ValueError:
            # 日時パースエラー等の場合はとりあえず進むか戻るか...ここではStep6へ
            return redirect('attendance_step6', application_id=application_id)


class AttendanceStep5LatenessView(AttendanceStepBaseView):
    """Step 5: 遅刻理由の入力 (遅刻時のみ)"""
    template_name = 'Work/attendance_step5.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

    def post(self, request, application_id):
        # 理由の保存
        reason = request.POST.get('lateness_reason_detail') # テキストエリア
        # 選択肢もあれば保存するが、今回はテキストエリアメインの画面
        self.update_session_data(application_id, {'lateness_reason_detail': reason})
        return redirect('attendance_step6', application_id=application_id)

class AttendanceStep6ConfirmView(AttendanceStepBaseView):
    """Step 6: 最終確認"""
    template_name = 'Work/attendance_step6.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        return render(request, self.template_name, {'application': application, 'data': session_data})

    def post(self, request, application_id):
        # DB保存
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        att_str = f"{session_data.get('attendance_date')} {session_data.get('attendance_time')}"
        leave_str = f"{session_data.get('leaving_date')} {session_data.get('leaving_time')}"
        
        correction_att = timezone.make_aware(datetime.strptime(att_str, '%Y-%m-%d %H:%M'))
        correction_leave = timezone.make_aware(datetime.strptime(leave_str, '%Y-%m-%d %H:%M'))
        
        AttendanceCorrection.objects.create(
            application=application,
            correction_attendance_at=correction_att,
            correction_leaving_at=correction_leave,
            correction_break_time=int(session_data.get('break_time', 0)),
            lateness_reason_detail=session_data.get('lateness_reason_detail', ''),
            status='pending'
        )
        
        # セッションクリア
        key = f'correction_data_{application_id}'
        if key in request.session:
            del request.session[key]
            
        return redirect('attendance_step7', application_id=application_id)

class AttendanceStep7FinishView(AttendanceStepBaseView):
    """Step 7: 完了画面"""
    template_name = 'Work/attendance_step7.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

class StoreReviewStep1View(LoginRequiredMixin, FormView):
    """Step 1: 評価選択 (Yes/No)"""
    form_class = StoreReviewStep1Form
    template_name = 'Work/store_review_step1.html'

    def dispatch(self, request, *args, **kwargs):
        application_id = self.kwargs.get('application_id')
        # 既にレビュー済みなら過去求人一覧へ (二重投稿防止)
        if StoreReview.objects.filter(job_application_id=application_id).exists():
             return redirect('past_jobs')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(JobApplication, id=self.kwargs['application_id'])
        context['application'] = application
        return context

    def form_valid(self, form):
        # 入力データをセッションに保存
        self.request.session['review_step1_data'] = form.cleaned_data
        return redirect('store_review_step2', application_id=self.kwargs['application_id'])

class StoreReviewStep2View(LoginRequiredMixin, FormView):
    """Step 2: コメント入力"""
    form_class = StoreReviewStep2Form
    template_name = 'Work/store_review_step2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(JobApplication, id=self.kwargs['application_id'])
        context['application'] = application
        return context

    def form_valid(self, form):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(JobApplication, id=application_id, worker=self.request.user)
        
        # セッションからStep1のデータを取得
        step1_data = self.request.session.get('review_step1_data', {})
        if not step1_data:
            return redirect('store_review_step1', application_id=application_id)

        # レビュー保存
        StoreReview.objects.create(
            job_application=application,
            worker=self.request.user,
            store=application.job_posting.template.store,
            comment=form.cleaned_data['comment'],
            is_time_matched=step1_data.get('is_time_matched'),
            is_content_matched=step1_data.get('is_content_matched'),
            is_want_to_work_again=step1_data.get('is_want_to_work_again')
        )
        
        # セッションクリア
        if 'review_step1_data' in self.request.session:
            del self.request.session['review_step1_data']
            
        return redirect('store_review_complete', application_id=application_id)

class StoreReviewCompleteView(LoginRequiredMixin, TemplateView):
    """Step 3: 完了画面"""
    template_name = 'Work/store_review_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(JobApplication, id=self.kwargs['application_id'])
        context['application'] = application
        context['store'] = application.job_posting.template.store
        context['step'] = 3  # Progress bar step
        return context
