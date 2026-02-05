import os
import django
import random
from datetime import date, timedelta, datetime
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, BusinessProfile
from django.utils import timezone
from django.contrib.auth.models import User

def generate_expansion_data():
    # 1. Get or Create Business Profile
    biz_profile = BusinessProfile.objects.first()
    if not biz_profile:
        print("No BusinessProfile found. Creating a dummy business.")
        user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.create_superuser('admin_seed', 'admin@example.com', 'adminpass')
        biz_profile = BusinessProfile.objects.create(
            user=user, company_name="拡張データ生成株式会社", business_type="corporation"
        )

    # 2. Add 3 stores in Saitama, Kanagawa, and Tokyo
    target_prefs_stores = ["埼玉県", "神奈川県", "東京都"]
    store_count = 0
    print("Adding 3 stores each in Saitama, Kanagawa, and Tokyo...")
    for pref in target_prefs_stores:
        for i in range(1, 4):
            store_name = f"{pref} 拠点店-{i}"
            city = "市区町村A"
            if pref == "東京都": city = "新宿区"
            elif pref == "神奈川県": city = "横浜市"
            elif pref == "埼玉県": city = "さいたま市"
            
            store, created = Store.objects.get_or_create(
                business=biz_profile,
                store_name=store_name,
                prefecture=pref,
                defaults={
                    'post_code': "0000000",
                    'city': city,
                    'address_line': f"{i}-1-1",
                    'industry': "その他"
                }
            )
            if created:
                store_count += 1
                print(f"  Created store: {store_name}")

    # 3. Add 5 jobs per day in 6 prefectures
    target_prefs_jobs = ["群馬県", "栃木県", "茨城県", "長野県", "山梨県", "静岡県"]
    job_count = 0
    today = date.today()
    days_to_generate = 14
    
    print("\nAdding 5 jobs per day in 6 prefectures...")
    titles = ["【新規】接客スタッフ募集", "未経験歓迎の簡単ワーク", "急募！配送アシスタント", "短期集中！イベント設営", "週末限定ワーク"]
    occupations = ["ホール", "キッチン", "品出し", "受付", "軽作業"]

    for pref in target_prefs_jobs:
        # Each prefecture needs at least one store for seeding jobs
        store, created = Store.objects.get_or_create(
            business=biz_profile,
            prefecture=pref,
            defaults={
                'store_name': f"{pref} 総合拠点",
                'post_code': "0000000",
                'city': "中心市",
                'address_line': "1-1",
                'industry': "サービス"
            }
        )
        if created:
            print(f"  Created base store for {pref}")

        for d in range(days_to_generate):
            work_date = today + timedelta(days=d)
            for j in range(5):
                title = titles[j % len(titles)]
                template = JobTemplate.objects.create(
                    store=store,
                    title=f"{pref} {title}",
                    industry="サービス",
                    occupation=occupations[j % len(occupations)],
                    work_content="地域での仕事です。未経験の方も大歓迎です。",
                    precautions="特になし",
                    belongings="筆記用具",
                    address=store.full_address,
                    contact_number="090-0000-0000"
                )

                start_hour = random.randint(9, 17)
                JobPosting.objects.create(
                    template=template,
                    work_date=work_date,
                    start_time=datetime.strptime(f"{start_hour:02d}:00", "%H:%M").time(),
                    end_time=datetime.strptime(f"{(start_hour+4):02d}:00", "%H:%M").time(),
                    title=template.title,
                    hourly_wage=1150,
                    transportation_fee=500,
                    recruitment_count=2,
                    application_deadline=timezone.make_aware(datetime.combine(work_date - timedelta(days=1), datetime.min.time()))
                )
                job_count += 1
        print(f"  Generated {days_to_generate * 5} jobs for {pref}")

    print(f"\n--- Seeding Complete ---")
    print(f"New Stores Created: {store_count}")
    print(f"New Job Postings Created: {job_count}")

if __name__ == "__main__":
    generate_expansion_data()
