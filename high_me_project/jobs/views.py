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
        
        # 有効な求人で、かつ緯度経度があるもの (テンプレートまたは店舗)
        jobs = JobPosting.objects.filter(
            Q(template__latitude__isnull=False) | Q(template__store__latitude__isnull=False),
            template__store__prefecture__in=target_prefs,
            visibility='public'
        ).select_related('template__store')
        
        # マップ表示用データ作成
        map_data = []
        for job in jobs:
            store = job.template.store
            # 緯度経度: テンプレート優先、なければ店舗
            lat = job.template.latitude if job.template.latitude else store.latitude
            lng = job.template.longitude if job.template.longitude else store.longitude

            # 座標がない場合はスキップ (フィルタで弾いているはずだが念のため)
            if lat is None or lng is None:
                continue

            map_data.append({
                'id': job.id,
                'title': job.title,
                'store_name': store.store_name,
                'lat': lat,
                'lng': lng,
                'url': reverse('job_detail', kwargs={'pk': job.id}),
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
        
        # 募集中の仕事のみ (デフォルトTrue)
        only_recruiting = session_filters.get('only_recruiting', True)
        if only_recruiting:
            # 1. 開始時間を過ぎていないもの (is_expired == False 相当)
            now = timezone.localtime(timezone.now())
            # selected_date が過去の場合は空にする
            if self.selected_date < self.today:
                queryset = queryset.none()
            # selected_date が今日の場合のみ、開始時間での比較が必要
            elif self.selected_date == self.today:
                queryset = queryset.filter(start_time__gt=now.time())
            
            # 2. 募集人数に達していないもの
            # JobPostingに matched_count property はあるが、DBクエリで直接扱うためにアノテーション等が必要
            # 今回は簡易的に、応募数との比較を行う (status='確定済み' のものをカウント)
            from django.db.models import Count, F
            queryset = queryset.annotate(
                confirmed_count=Count('applications', filter=Q(applications__status='確定済み'))
            ).filter(confirmed_count__lt=F('recruitment_count'))

        # 登録した資格が必要な仕事のみ
        qualification_only = session_filters.get('qualification_only', False)
        if qualification_only:
            queryset = queryset.filter(template__requires_qualification=True)
            
        # ソート処理
        sort_type = self.request.GET.get('sort', 'deadline') # デフォルトは「締切時刻が近い順」
        
        if sort_type == 'deadline':
            # 締切時刻が近い順 (勤務日 -> 開始時間)
            queryset = queryset.order_by('work_date', 'start_time')
        elif sort_type == 'current_location':
            # 現在地から近い順: 
            # サーバーサイドで正確にやるにはユーザーの現在地(lat/lng)をクエリパラメータで受け取る必要がある
            # ここでは簡易的に「保存されている緯度経度がある場合」の距離ソート、あるいはJS側での実装が必要だが
            # データベース参照とのことなので、一旦何もしないか、あるいはユーザー登録住所からの距離など仮実装
            # ※ユーザー要望では「データベースを参照して並び替え」
            pass 
        elif sort_type == 'specified_location':
             # 指定した場所から近い順
            pass
            
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
            'current_sort': self.request.GET.get('sort', 'deadline'), # 現在のソート順
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
    success_url = reverse_lazy('location_home')

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
            template__store__prefecture__in=target_prefs
        ).filter(
            Q(template__latitude__isnull=False) | Q(template__store__latitude__isnull=False)
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

        # 募集中の仕事のみ (デフォルトTrue)
        only_recruiting = session_filters.get('only_recruiting', True)
        if only_recruiting:
            # 1. 開始時間を過ぎていないもの (is_expired == False 相当)
            # MapViewのqsには既に work_date__gte=today が入っている
            now = timezone.localtime(timezone.now())
            # work_date が今日の場合のみ、開始時間での比較が必要
            qs = qs.exclude(work_date=now.date(), start_time__lte=now.time())
            
            # 2. 募集人数に達していないもの
            from django.db.models import Count, F
            qs = qs.annotate(
                confirmed_count=Count('applications', filter=Q(applications__status='確定済み'))
            ).filter(confirmed_count__lt=F('recruitment_count'))

        # 登録した資格が必要な仕事のみ
        qualification_only = session_filters.get('qualification_only', False)
        if qualification_only:
            qs = qs.filter(template__requires_qualification=True)
        
        jobs_data = []
        for job in qs:
            start_dt = datetime.combine(job.work_date, job.start_time)
            is_expired = timezone.make_aware(start_dt) < timezone.now()
            
            # 緯度経度: テンプレート優先
            lat = float(job.template.latitude) if job.template.latitude else float(job.template.store.latitude)
            lng = float(job.template.longitude) if job.template.longitude else float(job.template.store.longitude)

            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'work_date': job.work_date.strftime('%Y-%m-%d'),
                'start_time': job.start_time.strftime('%H:%M'),
                'end_time': job.end_time.strftime('%H:%M'),
                'lat': lat,
                'lng': lng,
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
        # 追加分: 募集中の仕事のみ / 資格が必要な仕事のみ
        context['only_recruiting'] = session_filters.get('only_recruiting', True)  # デフォルトTrue
        context['qualification_only'] = session_filters.get('qualification_only', False)

        # 遷移元情報を取得 (デフォルトはindex)
        context['from_view'] = self.request.GET.get('from', 'index')
        return context

    def post(self, request, *args, **kwargs):
        # 遷移元情報を維持
        from_view = request.POST.get('from', 'index')

        # "すべて解除" や 個別のリセット用
        if 'reset' in request.POST:
            if 'job_filters' in request.session:
                del request.session['job_filters']
            return redirect(f"{reverse('refine_home')}?from={from_view}")

        # 通常の更新 (チェックボックス等)
        filters = request.session.get('job_filters', {})
        filters['only_recruiting'] = 'only_recruiting' in request.POST
        filters['qualification_only'] = 'qualification_only' in request.POST
        request.session['job_filters'] = filters

        # 「絞り込み結果を表示」ボタンが押された場合、またはその動作を期待する場合
        # 既存通り index または map_view へ戻る
        if from_view == 'map_view':
            return redirect('map_view')
        return redirect('index')

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
            
            # Check if store is muted
            from business.models import StoreMute
            if hasattr(self.request.user, 'workerprofile'):
                context['is_muted'] = StoreMute.objects.filter(
                    worker=self.request.user.workerprofile,
                    store=job.template.store
                ).exists()
        
        context['is_applied'] = is_applied
        context['is_favorited'] = is_favorited
        context['is_closed'] = job.is_expired
        
        # 遷移元情報を取得
        context['from_view'] = self.request.GET.get('from', 'index')
        return context



class FavoriteJobsView(LoginRequiredMixin, TemplateView):
    template_name = 'Favorites/favorite_jobs.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # お気に入り求人
        favorite_jobs = FavoriteJob.objects.filter(user=self.request.user).select_related('job_posting', 'job_posting__template__store').order_by('-created_at')
        context['favorite_jobs'] = favorite_jobs
        context['tab'] = 'jobs'
        return context

class FavoriteStoresView(LoginRequiredMixin, TemplateView):
    template_name = 'Favorites/favorite_stores.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # お気に入り店舗
        favorite_stores = FavoriteStore.objects.filter(user=self.request.user).select_related('store').order_by('-created_at')
        context['favorite_stores'] = favorite_stores
        context['tab'] = 'stores'
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


class LongTermJobHistoryView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'Work/work_history_long_term.html'
    context_object_name = 'applications'

    def get_queryset(self):
        # 長期バイト (is_long_term=True) の応募履歴
        return JobApplication.objects.filter(
            worker=self.request.user, 
            job_posting__is_long_term=True
        ).select_related('job_posting', 'job_posting__template__store').order_by('-applied_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class WorkScheduleBaseView(LoginRequiredMixin, TemplateView):
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

class WorkScheduleUpcomingView(WorkScheduleBaseView):
    template_name = 'Work/work_upcoming.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # ユーザーの応募済み求人を全て取得（勤務日の昇順）
        applications = JobApplication.objects.filter(worker=self.request.user).select_related('job_posting', 'job_posting__template__store').order_by('job_posting__work_date', 'job_posting__start_time')
        
        upcoming = []
        for app in applications:
            job_end = timezone.make_aware(datetime.combine(app.job_posting.work_date, app.job_posting.end_time))
            # キャンセルや辞退は表示しない
            if app.status in ['辞退', 'キャンセル']:
                continue
            
            if not (app.status == '完了' or job_end < now or app.leaving_at):
                upcoming.append(app)

        context['upcoming_grouped'] = self.group_by_date(upcoming)
        context['tab'] = 'upcoming'
        return context

class WorkScheduleCompletedView(WorkScheduleBaseView):
    template_name = 'Work/work_completed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # ユーザーの応募済み求人を全て取得（勤務日の昇順）
        applications = JobApplication.objects.filter(
            worker=self.request.user
        ).select_related(
            'job_posting', 
            'job_posting__template__store'
        ).prefetch_related(
            'job_posting__template__photos'
        ).order_by('job_posting__work_date', 'job_posting__start_time')
        
        completed = []
        for app in applications:
            job_end = timezone.make_aware(datetime.combine(app.job_posting.work_date, app.job_posting.end_time))
            if app.status == '完了' or job_end < now or app.leaving_at:
                completed.append(app)

        context['completed_grouped'] = self.group_by_date(completed)
        context['tab'] = 'completed'
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

        # ペナルティ（利用停止中）の場合
        if profile.is_suspended:
            return render(request, 'Searchjobs/detail.html', {'job': job})

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

class JobCompletedDetailView(LoginRequiredMixin, TemplateView):
    """完了した仕事の詳細画面 (画像2のデザイン)"""
    template_name = 'Work/job_completed_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        # 完了した仕事
        application = get_object_or_404(JobApplication, job_posting_id=pk, worker=self.request.user)
        
        weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        weekday_jp = weekday_map[application.job_posting.work_date.weekday()]
        
        context['app'] = application
        context['weekday_jp'] = weekday_jp
        
        # 休憩時間 (実績があれば実績、なければ予定)
        break_minutes = application.actual_break_duration if application.actual_break_duration else application.job_posting.break_duration
        context['break_minutes'] = break_minutes
        
        # 最新の修正依頼を取得
        context['latest_correction'] = application.corrections.order_by('-created_at').first()

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
            # 実績休憩時間の初期値を設定 (勤務時間が休憩時間未満なら0、それ以外は予定時間)
            duration = (application.leaving_at - application.attendance_at).total_seconds() / 60
            default_break = application.job_posting.break_duration
            if duration > default_break:
                application.actual_break_duration = default_break
            else:
                application.actual_break_duration = 0
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
    template_name = 'Work/attendance/attendance_step1.html'

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
    template_name = 'Work/attendance/reward_confirm.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        
        posting = application.job_posting
        
        # モデルに実装した報酬計算メソッドを使用
        total_amount = application.get_calculated_reward()
        
        # 表示用に内訳を計算 (get_calculated_reward の中身と合わせる)
        duration_seconds = (application.leaving_at - application.attendance_at).total_seconds()
        break_minutes = application.actual_break_duration if application.actual_break_duration > 0 else posting.break_duration
        work_minutes = max(0, (duration_seconds / 60) - break_minutes)
        
        base_reward = int((work_minutes / 60) * posting.hourly_wage)
        transportation = posting.transportation_fee
        
        context = {
            'application': application,
            'base_reward': base_reward,
            'transportation': transportation,
            'total_amount': total_amount,
            'work_hours': round(work_minutes / 60, 1), # 表示用
        }
        return render(request, self.template_name, context)

    def post(self, request, application_id):
        application = self.get_application(application_id)
        
        # 報酬計算
        reward_amount = application.get_calculated_reward()
        
        # 勤怠情報の確定 (予定通りとして保存)
        # 完了状態にする
        application.status = '完了'
        application.is_reward_paid = True # 支払い済みフラグ
        application.save()

        # ウォレットに追加
        # ウォレットに追加
        from accounts.models import WalletTransaction
        WalletTransaction.objects.create(
            worker=application.worker.workerprofile,
            amount=reward_amount,
            transaction_type='reward',
            description=f"{application.job_posting.template.store.store_name} 報酬"
        )
        
        # 実績(EXP)の加算
        from accounts.services import AchievementService
        # 労働時間を計算 (分)
        if application.attendance_at and application.leaving_at:
            duration_seconds = (application.leaving_at - application.attendance_at).total_seconds()
            total_minutes = int(duration_seconds / 60)
            
            # 休憩時間は労働時間を超えないように制限 (テスト時などの短時間勤務対策)
            break_minutes_raw = application.actual_break_duration if application.actual_break_duration > 0 else application.job_posting.break_duration
            break_minutes = min(break_minutes_raw, total_minutes)
            
            work_minutes = max(0, total_minutes - break_minutes)
        else:
            work_minutes = 0

        earned_exp = AchievementService.calculate_exp_from_minutes(work_minutes)
        print(f"DEBUG: Adding EXP {earned_exp} to user {application.worker.username} (Work: {work_minutes}min)")
        AchievementService.add_exp(application.worker.workerprofile, earned_exp, "業務完了")
        
        # 完了画面ではなく評価入力画面のStep1へ
        return redirect('store_review_step1', application_id=application_id)

class RewardFinishView(AttendanceStepBaseView):
    """報酬確定完了画面"""
    template_name = 'Work/attendance/reward_finish.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

class AttendanceStep2GuideView(AttendanceStepBaseView):
    """Step 2: 修正依頼の流れ (ガイド画面)"""
    template_name = 'Work/attendance/attendance_step2.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})
        
    def post(self, request, application_id):
        return redirect('attendance_step3', application_id=application_id)

class AttendanceStep3TimeView(AttendanceStepBaseView):
    """Step 3: 業務開始・終了日時の入力"""
    template_name = 'Work/attendance/attendance_step3.html'

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
    template_name = 'Work/attendance/attendance_step4.html'

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
    template_name = 'Work/attendance/attendance_step5.html'

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
    template_name = 'Work/attendance/attendance_step6.html'

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
    template_name = 'Work/attendance/attendance_step7.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

class StoreReviewStep1View(LoginRequiredMixin, FormView):
    """Step 1: 評価選択 (Yes/No)"""
    form_class = StoreReviewStep1Form
    template_name = 'Work/store_review/store_review_step1.html'

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
        context['step'] = 1
        return context

    def form_valid(self, form):
        # 入力データをセッションに保存
        self.request.session['review_step1_data'] = form.cleaned_data
        return redirect('store_review_step2', application_id=self.kwargs['application_id'])

class StoreReviewStep2View(LoginRequiredMixin, FormView):
    """Step 2: コメント入力"""
    form_class = StoreReviewStep2Form
    template_name = 'Work/store_review/store_review_step2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(JobApplication, id=self.kwargs['application_id'])
        context['application'] = application
        context['step'] = 2
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
    template_name = 'Work/store_review/store_review_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(JobApplication, id=self.kwargs['application_id'])
        context['application'] = application
        context['store'] = application.job_posting.template.store
        context['step'] = 3  # Progress bar step
        return context

# --- キャンセル機能 ---
class JobCancelStep1PenaltyView(LoginRequiredMixin, TemplateView):
    """Step 1: キャンセル時のペナルティ確認"""
    template_name = 'Work/cancel/cancel_step1_penalty.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        context['application'] = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        return context

class JobCancelStep2ReasonView(LoginRequiredMixin, TemplateView):
    """Step 2: キャンセル理由選択"""
    template_name = 'Work/cancel/cancel_step2_reason.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        context['application'] = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        application_id = self.kwargs['application_id']
        reason = request.POST.get('reason')
        # Save to session
        request.session[f'cancel_reason_{application_id}'] = reason
        return redirect('job_cancel_step3', application_id=application_id)

class JobCancelStep3DetailView(LoginRequiredMixin, TemplateView):
    """Step 3: キャンセル理由詳細 (メッセージ入力)"""
    template_name = 'Work/cancel/cancel_step3_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        context['application'] = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        context['reason'] = self.request.session.get(f'cancel_reason_{application_id}', '')
        return context
    
    def post(self, request, *args, **kwargs):
        application_id = self.kwargs['application_id']
        reason_detail = request.POST.get('reason_detail')
        request.session[f'cancel_message_{application_id}'] = reason_detail
        return redirect('job_cancel_step4', application_id=application_id)

class JobCancelStep4InputView(LoginRequiredMixin, TemplateView):
    """Step 4: キャンセル内容確認 & 実行"""
    template_name = 'Work/cancel/cancel_step4_input.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        context['application'] = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        context['reason'] = self.request.session.get(f'cancel_reason_{application_id}', '')
        context['reason_detail'] = self.request.session.get(f'cancel_message_{application_id}', '')
        return context

    def post(self, request, *args, **kwargs):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        
        # キャンセル処理実行
        application.status = '辞退' # または 'cancelled'
        application.cancel_reason = request.POST.get('reason', '') # Formから再送、あるいはセッションから
        # モデルにフィールドがあれば保存
        # application.cancel_message = ...
        application.save()
        
        # ペナルティ付与 (8ポイント + 2週間停止)
        worker_profile = application.worker.workerprofile
        penalty_points = 8
        worker_profile.penalty_points += penalty_points
        from datetime import timedelta
        worker_profile.suspension_end_date = timezone.now() + timedelta(weeks=2)
        worker_profile.save()

        # 履歴保存
        from accounts.models import PenaltyHistory
        PenaltyHistory.objects.create(
            worker=worker_profile,
            points=penalty_points,
            total_points=worker_profile.penalty_points,
            reason="仕事をキャンセルしたため"
        )

        # 8ポイント以上の場合、他の確定済み求人をすべてキャンセル
        if worker_profile.penalty_points >= 8:
            other_apps = JobApplication.objects.filter(
                worker=application.worker,
                status='確定済み'
            ).exclude(pk=application.id)
            
            for app in other_apps:
                app.status = 'キャンセル' # または '辞退'
                app.cancel_reason = 'ペナルティによる自動キャンセル'
                app.save()
                # これらについてはペナルティを加算しない（多重ペナルティ防止）
        
        # セッションクリア
        keys = [f'cancel_reason_{application_id}', f'cancel_message_{application_id}']
        for k in keys:
            if k in request.session:
                del request.session[k]

        return redirect('work_schedule') # 完了後ははたらく画面へ


from business.models import AttendanceCorrection

class AttendanceCorrectionStatusView(LoginRequiredMixin, TemplateView):
    template_name = 'Work/attendance_correction_status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        application = get_object_or_404(JobApplication, pk=application_id, worker=self.request.user)
        
        # 最新の修正依頼を取得 (なければNone)
        correction = AttendanceCorrection.objects.filter(application=application).order_by('-created_at').first()
        
        context['application'] = application
        context['correction'] = correction
        
        # 戻るボタンの遷移先制御
        from_page = self.request.GET.get('from')
        if from_page == 'completed_detail':
            context['back_url'] = reverse('job_completed_detail', kwargs={'pk': application.job_posting.id})
        else:
            context['back_url'] = reverse('job_working_detail', kwargs={'pk': application.job_posting.id})
            
        return context

