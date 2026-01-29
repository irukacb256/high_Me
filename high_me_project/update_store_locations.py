
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store

# 大宮駅周辺の緯度経度
BASE_LAT = 35.9063
BASE_LNG = 139.6240

def update_locations():
    stores = Store.objects.all()
    print(f"Updating locations for {stores.count()} stores...")
    
    for store in stores:
        # ランダムに少しずらす (約km圏内)
        # 0.01度 ≒ 1km
        lat_offset = random.uniform(-0.03, 0.03)
        lng_offset = random.uniform(-0.03, 0.03)
        
        store.latitude = BASE_LAT + lat_offset
        store.longitude = BASE_LNG + lng_offset
        store.save()
        print(f"Updated {store.store_name}: {store.latitude}, {store.longitude}")

if __name__ == '__main__':
    update_locations()
