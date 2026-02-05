import os
import django
import sys
from django.db import transaction

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile, Store

# 対象とする地域プレフィックス
REGIONS = ['chiba', 'saitama', 'kanagawa', 'ibaraki', 'gunma', 'tochigi', 'tokyo', 'yamanashi', 'nagano', 'shizuoka']

def cleanup():
    print("Starting cleanup of duplicated regional users...")
    
    deleted_count = 0
    with transaction.atomic():
        for prefix in REGIONS:
            username_with_at = f"{prefix}@example.com"
            
            # '@'付きのユーザーが存在するか確認
            try:
                user_at = User.objects.get(username=username_with_at)
                
                # '@'なしのユーザー（正規版）が存在するか確認
                if User.objects.filter(username=prefix).exists():
                    # 安全確認：'@'付きの方に店舗が紐付いていないことを確認
                    stores_count = 0
                    if hasattr(user_at, 'businessprofile'):
                        stores_count = user_at.businessprofile.store_set.count()
                    
                    if stores_count == 0:
                        print(f"Deleting duplicated user: {username_with_at} (ID:{user_at.id})")
                        user_at.delete()
                        deleted_count += 1
                    else:
                        print(f"WARNING: User {username_with_at} has stores! Skipping deletion. Please merge manually.")
                else:
                    print(f"User {username_with_at} exists but no duplicate {prefix} found. Skipping.")
            except User.DoesNotExist:
                pass

    print(f"Cleanup completed. Total users deleted: {deleted_count}")

if __name__ == "__main__":
    cleanup()
