
import os
import django
import sys
import datetime
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication
from accounts.models import WorkerProfile, WalletTransaction

def backfill_rewards():
    print("Starting reward transaction backfill...")
    
    # 完了済みの応募を取得
    apps = JobApplication.objects.filter(status='完了')
    
    count = 0
    for app in apps:
        if not hasattr(app.worker, 'workerprofile'):
            print(f"Skipping app {app.id}: User {app.worker.username} has no workerprofile.")
            continue
            
        worker_profile = app.worker.workerprofile
        
        # すでにこの求人に対する報酬履歴があるかチェック (説明文で判定)
        desc = f"{app.job_posting.template.store.store_name} 報酬"
        if WalletTransaction.objects.filter(worker=worker_profile, description__icontains=app.job_posting.template.store.store_name, amount=app.get_calculated_reward()).exists():
            # 簡易的な重複チェック。本当はJobApplicationへのFKがあるとベストだが、現状のモデルに合わせる
            continue
            
        reward_amount = app.get_calculated_reward()
        if reward_amount <= 0:
            continue
            
        # 取引作成
        # created_at は auto_now_add なので、後で手動更新する
        tx = WalletTransaction.objects.create(
            worker=worker_profile,
            amount=reward_amount,
            transaction_type='reward',
            description=f"{app.job_posting.template.store.store_name} 報酬 (バックフィル)"
        )
        
        # 求人の実施日（終了時間）に合わせる
        target_date = app.leaving_at or timezone.make_aware(datetime.datetime.combine(app.job_posting.work_date, datetime.datetime.min.time()))
        
        tx.created_at = target_date
        tx.save()
        
        count += 1
        print(f"Created tx: {worker_profile.user.username} - {reward_amount} yen - Date: {target_date.date()}")

    print(f"Backfill completed. Total transactions created: {count}")

if __name__ == '__main__':
    backfill_rewards()
