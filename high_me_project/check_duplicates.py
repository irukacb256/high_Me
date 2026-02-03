import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import ChatRoom
from django.db.models import Count

print(f"Checking for duplicates in ChatRoom (store, worker)...")
duplicates = ChatRoom.objects.values('store', 'worker').annotate(count=Count('id')).filter(count__gt=1)

if duplicates.exists():
    print(f"Found {duplicates.count()} duplicate pairs.")
    for d in duplicates:
        print(f"Store ID: {d['store']}, Worker ID: {d['worker']}, Count: {d['count']}")
        rooms = ChatRoom.objects.filter(store_id=d['store'], worker_id=d['worker'])
        for r in rooms:
            print(f" - Room ID: {r.id}, Created: {r.created_at}")
else:
    print("No duplicates found for (store, worker). Unique constraint is holding.")

print("\nChecking rooms per business for same worker...")
# Assuming we want to know if a BUSINESS has multiple rooms for SAME WORKER (across stores)
rooms = ChatRoom.objects.all().select_related('store', 'worker', 'store__business')
from collections import defaultdict
biz_worker_map = defaultdict(list)
for r in rooms:
    key = (r.store.business.id, r.worker.id)
    biz_worker_map[key].append(r)

for (biz_id, worker_id), room_list in biz_worker_map.items():
    if len(room_list) > 1:
        print(f"Business {biz_id}, Worker {worker_id} has {len(room_list)} rooms:")
        for r in room_list:
            print(f" - Room ID: {r.id}, Store: {r.store.store_name} (ID: {r.store.id})")
