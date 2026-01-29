
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication, ChatRoom, Store
from django.contrib.auth import get_user_model

def create_chat_rooms():
    # 確定済みの申し込みを取得
    apps = JobApplication.objects.filter(status='確定済み').select_related('job_posting__template__store', 'worker')
    
    count = 0
    for app in apps:
        store = app.job_posting.template.store
        worker = app.worker
        
        # Roomを作成（なければ）
        room, created = ChatRoom.objects.get_or_create(
            store=store,
            worker=worker
        )
        if created:
            count += 1
            print(f"Created chat room for {store.store_name} - {worker.get_full_name()}")
            
    print(f"Total {count} chat rooms created.")

if __name__ == '__main__':
    create_chat_rooms()
