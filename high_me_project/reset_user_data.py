import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import JobApplication, ChatRoom
from accounts.models import WorkerProfile, WalletTransaction, ExpHistory, WorkerMembership

def reset_user_data(phone_number):
    user = User.objects.filter(username=phone_number).first()
    if not user:
        print(f"User with phone {phone_number} not found.")
        return

    print(f"Resetting data for User: {user.username} (ID: {user.id})")
    
    try:
        profile = user.workerprofile
    except WorkerProfile.DoesNotExist:
        print("WorkerProfile not found.")
        return

    # 1. 応募データの削除 (カスケード削除によりレビューや修正依頼も削除される)
    apps = JobApplication.objects.filter(worker=user)
    app_count = apps.count()
    apps.delete()
    print(f"Deleted {app_count} applications.")

    # 2. ウォレット取引履歴の削除
    transactions = WalletTransaction.objects.filter(worker=profile)
    trans_count = transactions.count()
    transactions.delete()
    print(f"Deleted {trans_count} wallet transactions.")

    # 3. 経験値履歴の削除
    exps = ExpHistory.objects.filter(worker=profile)
    exp_count = exps.count()
    exps.delete()
    print(f"Deleted {exp_count} EXP histories.")

    # 4. メンバーシップのリセット
    membership, created = WorkerMembership.objects.get_or_create(worker=profile)
    membership.grade = 'ROOKIE'
    membership.level = 0
    membership.current_exp = 0
    membership.save()
    print("Reset WorkerMembership to ROOKIE Lv.0.")

    # 5. チャットルームの削除
    rooms = ChatRoom.objects.filter(worker=user)
    room_count = rooms.count()
    rooms.delete()
    print(f"Deleted {room_count} chat rooms.")

    print("Reset completed successfully.")

if __name__ == "__main__":
    reset_user_data('09011112222')
