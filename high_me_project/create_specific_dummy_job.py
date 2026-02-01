
import os
import django
from datetime import date, time, datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting
from django.utils import timezone

def create_specific_job():
    # 1. Storeを取得
    store = Store.objects.first()
    if not store:
        print("Error: No store found.")
        return

    print(f"Using Store: {store.store_name}")

    # 2. Templateを取得 (なければ簡易作成)
    template = JobTemplate.objects.filter(store=store).first()
    if not template:
        template = JobTemplate.objects.create(
            store=store,
            title="テスト用テンプレート",
            industry="飲食",
            occupation="ホール",
            work_content="ホール業務全般",
            precautions="遅刻厳禁",
            address=store.full_address,
            contact_number="090-0000-0000"
        )

    # 3. JobPostingを作成
    # 時間: 23:30 - 23:45 (当日)
    today = timezone.now().date()
    start_time = time(23, 30)
    end_time = time(23, 45)
    
    posting = JobPosting.objects.create(
        template=template,
        work_date=today,
        start_time=start_time,
        end_time=end_time,
        title="【テスト】23:30-23:45 短時間業務",
        work_content="動作確認用の短時間業務です。",
        is_long_term=False,
        hourly_wage=1200,
        transportation_fee=500,
        recruitment_count=5,
        visibility='public'
    )
    
    print(f"Created Job: {posting.title} ({posting.work_date} {posting.start_time}-{posting.end_time})")

if __name__ == '__main__':
    create_specific_job()
