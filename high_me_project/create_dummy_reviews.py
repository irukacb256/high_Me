import os
import django
import random
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobPosting, JobApplication, StoreReview
from django.contrib.auth.models import User

def create_reviews():
    print("Creating dummy reviews...")
    
    # 店舗取得 (ID=1)
    store = Store.objects.first()
    if not store:
        print("Store not found.")
        return

    print(f"Target Store: {store.store_name}")

    # 既存のレビューを全削除 (間違ったデータがあればクリア)
    StoreReview.objects.all().delete()
    print("Deleted all existing comments.")

    # ワーカー取得 (WorkerProfileを持つユーザーのみ)
    # create_dummy_reviews.py実行前にWorkerProfileが作成されている前提
    # 安全のため、WorkerProfileが存在するユーザーに限定
    workers = User.objects.filter(workerprofile__isnull=False)
    
    if not workers.exists():
        print("No workers with profile found.")
        return

    print(f"Found {workers.count()} workers.")

    # 求人取得 (過去のもの)
    postings = JobPosting.objects.filter(template__store=store)
    
    # レビュー作成
    count = 0
    for worker in workers:
        # 適当な求人に応募させる（なければ作成）
        posting = postings.first()
        if not posting:
            print("No job postings found.")
            break
            
        application, created = JobApplication.objects.get_or_create(
            job_posting=posting,
            worker=worker,
            defaults={'status': '完了', 'attendance_at': timezone.now(), 'leaving_at': timezone.now()}
        )
        
        # 既にレビューがあるか確認
        if hasattr(application, 'store_review'):
            continue
            
        # レビューデータ作成
        is_good = random.choice([True, True, True, False]) # 75% Good
        
        review = StoreReview.objects.create(
            job_application=application,
            store=store,
            worker=worker,
            is_time_matched=is_good, # ランダムに
            is_content_matched=True,
            is_want_to_work_again=is_good,
            comment=f"店舗の方の対応がとても丁寧で、初めてでも安心して働けました！\nまた募集があれば応募したいです。" if is_good else "事前に聞いていた業務内容と少し異なる点があり、戸惑いました。\n忙しいのは分かりますが、説明はきちんとしてほしかったです。"
        )
        print(f"Created review from {worker.username}")
        count += 1
        
        if count >= 5:
            break
            
    print(f"Created {count} reviews.")

if __name__ == '__main__':
    create_reviews()
