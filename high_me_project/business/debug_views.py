from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from business.models import Store, JobTemplate, JobPosting, JobApplication
import datetime

class DebugSetupReviewView(View):
    def get(self, request):
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
                'recruitment_count': 1,
            }
        )
        # Ensure additional fields are set if created or existing but empty
        if not posting.work_content:
            posting.work_content = "ホール業務全般"
            posting.save()
        
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
