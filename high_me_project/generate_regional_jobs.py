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

def generate_regional():
    # Target prefectures
    prefectures = ["群馬県", "栃木県", "茨城県", "長野県", "山梨県"]
    
    # Existing Business Profile for linking stores
    biz_profile = BusinessProfile.objects.first()
    if not biz_profile:
        print("No BusinessProfile found. Creating a dummy business first.")
        user = User.objects.filter(is_staff=True).first()
        biz_profile = BusinessProfile.objects.create(
            user=user, company_name="地域展開株式会社", business_type="corporation"
        )

    # Data lists
    store_names = {
        "群馬県": ["高崎カフェ", "前橋レストラン", "伊勢崎ストア"],
        "栃木県": ["宇都宮餃子店", "小山ショップ", "足利モール"],
        "茨城県": ["水戸ベーカリー", "つくばラボ店", "日立マート"],
        "長野県": ["松本信州そば", "長野駅前カフェ", "上田マーケット"],
        "山梨県": ["甲府ほうとう店", "富士吉田ブティック", "笛吹ワイナリー直営店"]
    }
    
    cities = {
        "群馬県": "高崎市", "栃木県": "宇都宮市", "茨城県": "水戸市", "長野県": "長野市", "山梨県": "甲府市"
    }

    titles = ["【地域限定】スタッフ募集", "未経験歓迎のお仕事", "短期アルバイト募集", "週末のみOK！接客スタッフ"]
    industries = ["飲食", "小売", "サービス"]
    occupations = ["ホール", "キッチン", "品出し", "受付"]
    
    today = date.today()
    target_date = date(2026, 2, 28)
    
    print("Generating jobs for new regions...")

    for pref in prefectures:
        # 1. Create a store for each prefecture if not exists
        store_name = random.choice(store_names[pref])
        store, created = Store.objects.get_or_create(
            business=biz_profile,
            prefecture=pref,
            city=cities[pref],
            defaults={
                'store_name': store_name,
                'post_code': "0000000",
                'address_line': "1-2-3",
                'industry': random.choice(industries)
            }
        )
        if created:
            print(f"Created new store: {store_name} in {pref}")

        # 2. Create Job Postings
        current_date = today
        for i in range(10): # Create 10 jobs per prefecture
            work_date = current_date + timedelta(days=i)
            
            template = JobTemplate.objects.create(
                store=store,
                title=f"{pref} {random.choice(titles)}",
                industry=store.industry,
                occupation=random.choice(occupations),
                work_content="地域密着型のお仕事です。丁寧な指導があるので安心してください。",
                precautions="元気な挨拶をお願いします。",
                belongings="筆記用具",
                address=store.full_address,
                contact_number="090-0000-0000"
            )

            start_hour = random.randint(10, 16)
            JobPosting.objects.create(
                template=template,
                work_date=work_date,
                start_time=datetime.strptime(f"{start_hour:02d}:00", "%H:%M").time(),
                end_time=datetime.strptime(f"{(start_hour+4):02d}:00", "%H:%M").time(),
                title=template.title,
                hourly_wage=1200,
                transportation_fee=500,
                recruitment_count=2,
                application_deadline=timezone.make_aware(datetime.combine(work_date - timedelta(days=1), datetime.min.time()))
            )
            
    print("Finished generating regional jobs.")

if __name__ == "__main__":
    generate_regional()
