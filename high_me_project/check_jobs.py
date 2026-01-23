
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobPosting

def check_data():
    print("--- 求人データ確認 ---")
    postings = JobPosting.objects.all().order_by('work_date')
    count = postings.count()
    print(f"総求人数: {count}")
    
    if count == 0:
        print("求人データが1件もありません。店舗管理画面から作成してください。")
    else:
        for p in postings:
            print(f"ID: {p.id}")
            print(f"  タイトル: {p.title}")
            print(f"  日付: {p.work_date} (今日: {timezone.now().date()})")
            print(f"  公開状態: {p.is_published}")
            print(f"  テンプレートID: {p.template_id}")
            print("-" * 20)

if __name__ == '__main__':
    check_data()
