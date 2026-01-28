import os
import sys
import django
import random
from datetime import date, timedelta, datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from django.conf import settings
from business.models import BusinessProfile, Store, JobTemplate, JobPosting, JobApplication
from accounts.models import WorkerProfile

def rebuild_database():
    print("=== Rebuilding Database ===")

    # 1. Delete DB file
    db_file = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    if os.path.exists(db_file):
        print(f"Removing {db_file}...")
        try:
            os.remove(db_file)
        except PermissionError:
            print("Error: Cannot delete db.sqlite3. Is the server running? Please stop the server and try again.")
            return
    else:
        print("db.sqlite3 not found, skipping delete.")

    # 2. Migrate
    print("Running migrations...")
    call_command('migrate')

    # 3. Create Superusers
    print("Creating superusers...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superuser 'admin' created (password: admin)")
    
    if not User.objects.filter(username='iruka').exists():
        User.objects.create_superuser('iruka', 'iruka@example.com', 'password')
        print("Superuser 'iruka' created (password: password)")

    # 4. Populate Business Data
    print("Populating Business Data...")
    businesses = [
        {'username': 'chiba@example.com', 'company': '千葉ロジスティクス', 'type': '物流', 'store': '船橋倉庫', 'pref': '千葉県'},
        {'username': 'saitama@example.com', 'company': '埼玉カフェグループ', 'type': '飲食', 'store': '大宮カフェテラス', 'pref': '埼玉県'},
        {'username': 'kanagawa@example.com', 'company': '横浜イベント株式会社', 'type': 'イベント', 'store': '横浜アリーナ整理', 'pref': '神奈川県'},
    ]

    for biz_data in businesses:
        u, _ = User.objects.get_or_create(username=biz_data['username'])
        u.email = biz_data['username'] # Ensure email matches username for convenience
        u.set_password('password')
        u.save()
        
        bp, _ = BusinessProfile.objects.get_or_create(user=u, defaults={
            'company_name': biz_data['company'], 'business_type': biz_data['type']
        })
        
        store, _ = Store.objects.get_or_create(business=bp, store_name=biz_data['store'], defaults={
            'post_code': '273-0001', 'prefecture': biz_data['pref'], 'city': 'テスト市', 'address_line': '1-1'
        })
        
        # Template
        template, _ = JobTemplate.objects.get_or_create(store=store, title=f"{biz_data['store']} スタッフ募集", defaults={
            'industry': biz_data['type'], 'occupation': '軽作業', 'work_content': '誰でも簡単な軽作業です', 'address': f"{biz_data['pref']} テスト市 1-1",
            'contact_number': '090-0000-0000', 'has_unexperienced_welcome': True
        })
        
        # Postings for next 7 days
        today = date.today()
        for i in range(7):
            work_date = today + timedelta(days=i)
            JobPosting.objects.get_or_create(template=template, work_date=work_date, defaults={
                'start_time': '09:00', 'end_time': '18:00', 'title': f"{biz_data['store']} 募集 {i+1}日目",
                'hourly_wage': 1200, 'recruitment_count': 5, 'is_published': True
            })

    # 5. Populate Worker Data
    print("Populating Worker Data...")
    workers = [
        # (Username/Phone, Last, First, LastKana, FirstKana, Gender, Verified)
        ('09011112222', '佐藤', '健', 'サトウ', 'タケル', '男性', True),
        ('09033334444', '鈴木', '花子', 'スズキ', 'ハナコ', '女性', True),
        ('08055556666', '田中', '一郎', 'タナカ', 'イチロウ', '男性', False), # Unverified user
    ]

    worker_objs = []
    for username, last, first, last_k, first_k, gender, is_verified in workers:
        u, _ = User.objects.get_or_create(username=username)
        u.set_password('password')
        u.save()
        
        wp, _ = WorkerProfile.objects.get_or_create(user=u, defaults={
            'last_name_kanji': last, 'first_name_kanji': first,
            'last_name_kana': last_k, 'first_name_kana': first_k,
            'gender': gender, 
            # 20代〜40代で分散させる
            'birth_date': date(random.randint(1980, 2005), random.randint(1, 12), random.randint(1, 28)),
            'is_setup_completed': True, 
            'is_identity_verified': is_verified
        })
        worker_objs.append(u)

    # 6. Create Applications
    print("Creating Applications...")
    postings = JobPosting.objects.all()
    if postings.exists():
        for i, worker in enumerate(worker_objs):
            # Apply to random jobs
            target_posting = postings[i % postings.count()]
            JobApplication.objects.get_or_create(job_posting=target_posting, worker=worker, defaults={'status': '確定済み'})

    print("=== Rebuild Complete ===")

if __name__ == '__main__':
    rebuild_database()
