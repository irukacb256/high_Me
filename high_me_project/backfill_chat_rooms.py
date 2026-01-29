
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication, ChatRoom

print("--- Backfilling ChatRooms ---")
apps = JobApplication.objects.all()
count = 0
created_count = 0

for app in apps:
    store = app.job_posting.template.store
    worker = app.worker
    
    room, created = ChatRoom.objects.get_or_create(
        store=store,
        worker=worker
    )
    
    if created:
        created_count += 1
        # print(f"Created room for {store.store_name} - {worker.username}")
    
    count += 1

print(f"Processed {count} applications.")
print(f"Created {created_count} new chat rooms.")
