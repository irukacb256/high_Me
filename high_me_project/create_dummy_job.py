
import os
import django
from datetime import date, time, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting
from django.utils import timezone

def create_dummy_job():
    # 1. Storeを取得 (なければエラーになるので、存在する前提だが、なければ作成するロジックもアリ)
    store = Store.objects.first()
    if not store:
        print("Error: No store found. Please verify store exists.")
        return

    print(f"Using Store: {store.store_name}")

    # 2. Templateを取得 (なければ作る)
    template = JobTemplate.objects.filter(store=store).first()
    if not template:
        # 簡易作成
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
        print("Created new template.")

    # 3. JobPostingを作成
    # 時間: 21:15 - 22:15 (当日)
    today = timezone.now().date()
    start_time = time(21, 15)
    end_time = time(22, 15)
    
    # 既存の同日同時刻の求人があれば重複作成を避けるか、あえて作るか...今回はユーザー要望で「追加」なので作る
    
    posting = JobPosting.objects.create(
        template=template,
        work_date=today,
        start_time=start_time,
        end_time=end_time,
        title="【急募】ディナータイムのホールスタッフ",
        work_content="お客様のご案内、オーダー取り、配膳、片付けなど、ホール業務全般をお願いします。",
        is_long_term=False,
        hourly_wage=1200,
        transportation_fee=500,
        recruitment_count=3,
        visibility='public'
    )
    
    print(f"Created JobPosting: {posting.title} ({posting.work_date} {posting.start_time}-{posting.end_time})")

if __name__ == '__main__':
    create_dummy_job()
