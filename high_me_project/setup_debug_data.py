import os
import django
import sys
import datetime

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import Store, JobTemplate, JobPosting, JobApplication
from django.utils import timezone

def setup_debug_data():
    # 1. Store
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
    
    # Always set name for debug purposes
    worker.last_name = "山田"
    worker.first_name = "太郎"
    worker.save()

    # 3. JobTemplate
    # Corrected fields based on actual model definition
    template, _ = JobTemplate.objects.get_or_create(
        store=store,
        title="デバッグ用ホールスタッフ募集",
        defaults={
            'industry': '飲食・フード',
            'occupation': 'ホール',
            'work_content': "ホール業務全般、接客、配膳など",
            'precautions': "特になし",
            'address': "千葉市美浜区ひび野2-110",
            'contact_number': "090-0000-0000",
            # Removed invalid fields like hourly_wage from Template
        }
    )

    # 4. JobPosting
    today = timezone.now().date()
    posting, _ = JobPosting.objects.get_or_create(
        template=template,
        work_date=today,
        defaults={
            'title': "【急募】ランチタイムホールスタッフ",
            'start_time': datetime.time(10, 0),
            'end_time': datetime.time(15, 0),
            'hourly_wage': 1200,
            'transportation_fee': 500,
            'recruitment_count': 1,
            'work_content': "ホール業務全般"
        }
    )
    
    # 5. JobApplication
    app, _ = JobApplication.objects.get_or_create(
        job_posting=posting,
        worker=worker,
        defaults={'status': '確定済み'}
    )
    
    if not app.attendance_at:
        app.attendance_at = timezone.now() - datetime.timedelta(hours=5)
    if not app.leaving_at:
        app.leaving_at = timezone.now() - datetime.timedelta(minutes=10)
    
    app.status = '確定済み'
    app.save()

    print("-" * 30)
    print("DEBUG DATA SETUP COMPLETE")
    # Using hardcoded ID retrieval for URL construction locally
    url = f"/biz/store/{store.id}/reviews/{posting.id}/"
    print(f"Review URL: http://127.0.0.1:8000{url}")
    print("-" * 30)

if __name__ == "__main__":
    setup_debug_data()
