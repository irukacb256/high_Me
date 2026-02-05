import os
import django
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Notification

def seed_notifs():
    users = User.objects.all()
    if not users.exists():
        print("No users found.")
        return

    sample_notifs = [
        {
            "title": "アプリが新しくなりました！",
            "content": "いつもHigh Meをご利用いただきありがとうございます。\nアプリのデザインを大幅に刷新しました。より使いやすくなったHigh Meをぜひお楽しみください。"
        },
        {
            "title": "【重要】システムメンテナンスのお知らせ",
            "content": "下記の日程でシステムメンテナンスを実施いたします。\n\n日時：2026年2月15日 02:00〜05:00\n\nメンテナンス中はアプリのすべての機能がご利用いただけません。ご不便をおかけしますが、ご理解のほどよろしくお願いいたします。"
        }
    ]

    for user in users:
        for item in sample_notifs:
            Notification.objects.get_or_create(
                user=user,
                title=item["title"],
                defaults={"content": item["content"]}
            )
    
    print(f"Seed completed for {users.count()} users.")

if __name__ == "__main__":
    seed_notifs()
