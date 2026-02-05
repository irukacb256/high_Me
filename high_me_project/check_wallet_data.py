
import os
import django
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

# Django初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import WorkerProfile, WalletTransaction

def check_data():
    # 最初のワーカープロファイルを取得（テスト用）
    profile = WorkerProfile.objects.first()
    if not profile:
        print("No worker profile found.")
        return

    print(f"Checking data for worker: {profile.user.username}")
    
    # 全取引
    total_tx = profile.wallet_transactions.count()
    print(f"Total transactions: {total_tx}")
    
    # 報酬タイプ
    reward_tx = profile.wallet_transactions.filter(transaction_type='reward')
    print(f"Reward transactions: {reward_tx.count()}")
    
    for tx in reward_tx:
        print(f" - Date: {tx.created_at}, Amount: {tx.amount}, Desc: {tx.description}")
        
    # 今月の報酬
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly = reward_tx.filter(created_at__gte=start_of_month).aggregate(Sum('amount'))['amount__sum'] or 0
    print(f"Monthly reward (this month): {monthly}")

if __name__ == "__main__":
    check_data()
