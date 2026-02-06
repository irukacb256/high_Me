
import os
import django
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile, Store, JobTemplate, JobPosting

def run():
    print("Starting Cat Search job seeding...")
    
    # 1. Create User
    username = 'cat_finder_biz'
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password='password123', email='cat@example.com')
        print(f"User {username} created.")
    else:
        user = User.objects.get(username=username)
        print(f"User {username} already exists.")

    # 2. BusinessProfile
    biz, created = BusinessProfile.objects.get_or_create(
        user=user,
        defaults={
            'company_name': '猫探し調査団',
            'business_type': 'サービス業',
            'industry': 'その他',
            'post_code': '1540001',
            'prefecture': '東京都',
            'city': '世田谷区',
            'address_line': '世田谷1-1-1'
        }
    )
    print(f"BusinessProfile: {biz.company_name} (Created: {created})")

    # 3. Store
    store, created = Store.objects.get_or_create(
        business=biz,
        store_name='世田谷本部',
        defaults={
            'industry': 'その他',
            'post_code': '1540001',
            'prefecture': '東京都',
            'city': '世田谷区',
            'address_line': '世田谷1-1-1',
            'latitude': 35.6465,
            'longitude': 139.6533
        }
    )
    print(f"Store: {store.store_name} (Created: {created})")

    # 4. JobTemplate
    template, created = JobTemplate.objects.get_or_create(
        store=store,
        title='【緊急・高額】迷い猫の捜索協力',
        defaults={
            'industry': '軽作業',
            'occupation': '捜索スタッフ',
            'work_content': '大切にしている猫がいなくなってしまいました。住宅街や公園などを中心に捜索のお手伝いをお願いします。',
            'precautions': '猫を見つけても無理に追いかけないでください。特に入門時の講習等はありません。',
            'requirements': '穏やかに猫に接することができる方',
            'belongings': '動きやすい服装',
            'address': '東京都世田谷区世田谷1-1-1',
            'access': '東急田園都市線 三軒茶屋駅 徒歩5分',
            'contact_number': '090-0000-0000',
            'latitude': 35.6465,
            'longitude': 139.6533
        }
    )
    print(f"JobTemplate: {template.title} (Created: {created})")

    # 5. JobPosting for Feb 11th, 2026
    work_date = date(2026, 2, 11)
    # 20,000 yen for 5 hours = 100,000 yen
    start_time = time(10, 0)
    end_time = time(15, 0)
    
    posting, created = JobPosting.objects.get_or_create(
        template=template,
        work_date=work_date,
        defaults={
            'start_time': start_time,
            'end_time': end_time,
            'title': template.title,
            'work_content': template.work_content,
            'hourly_wage': 20000,
            'transportation_fee': 1000,
            'recruitment_count': 3,
            'break_duration': 0,
            'is_published': True
        }
    )
    print(f"JobPosting: {posting.work_date} {posting.start_time}-{posting.end_time} (Created: {created})")

if __name__ == '__main__':
    run()
