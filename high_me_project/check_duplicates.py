import os
import django
import sys

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile, Store

def check_users():
    print("Checking users with '@' in username...")
    users = User.objects.filter(username__contains='@')
    for u in users:
        has_profile = hasattr(u, 'businessprofile')
        stores_count = 0
        if has_profile:
            stores_count = u.businessprofile.store_set.count()
        
        # 名前部分（@の前）だけでユーザーが存在するか確認
        name_only = u.username.split('@')[0]
        duplicate_exists = User.objects.filter(username=name_only).exists()
        
        print(f"ID:{u.id} | Username:{u.username} | Profile:{has_profile} | Stores:{stores_count} | Duplicate({name_only}) Exists:{duplicate_exists}")

if __name__ == "__main__":
    check_users()
