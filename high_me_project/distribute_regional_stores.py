import os
import django
import random
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, BusinessProfile

# 各県の拠点都市と座標
DIVERSE_LOCATIONS = {
    "群馬県": [
        ("高崎市八島町", 36.3219, 139.0033),
        ("前橋市本町", 36.3895, 139.0634),
        ("伊勢崎市日の出町", 36.3222, 139.1975),
        ("太田市飯田町", 36.2917, 139.3764)
    ],
    "栃木県": [
        ("宇都宮市馬場通り", 36.5658, 139.8836),
        ("小山市中央町", 36.3147, 139.8003),
        ("足利市田中町", 36.3333, 139.4500),
        ("栃木市万町", 36.3833, 139.7333)
    ],
    "茨城県": [
        ("水戸市宮町", 36.3659, 140.4714),
        ("つくば市吾妻", 36.0835, 140.0764),
        ("日立市幸町", 36.5917, 140.6500),
        ("土浦市中央", 36.0833, 140.2000)
    ],
    "長野県": [
        ("長野市南長野", 36.6485, 138.1942),
        ("松本市中央", 36.2378, 137.9719),
        ("上田市天神", 36.4000, 138.2500),
        ("飯田市本町", 35.5167, 137.8167)
    ],
    "山梨県": [
        ("甲府市丸の内", 35.6663, 138.5683),
        ("富士吉田市上吉田", 35.4872, 138.8044),
        ("笛吹市石和町", 35.6500, 138.6333),
        ("南アルプス市", 35.6000, 138.4667)
    ],
    "静岡県": [
        ("静岡市葵区黒金町", 34.9756, 138.3828),
        ("浜松市中区砂山町", 34.7038, 137.7348),
        ("沼津市大手町", 35.1017, 138.8597),
        ("富士市本町", 35.1500, 138.6833)
    ]
}

def distribute_stores():
    print("Distributing stores across regional cities...")
    biz_profile = BusinessProfile.objects.first()
    if not biz_profile:
        print("Error: No BusinessProfile found.")
        return

    # 対象地域の JobTemplate を取得
    target_prefs = DIVERSE_LOCATIONS.keys()
    templates = JobTemplate.objects.filter(store__prefecture__in=target_prefs)
    
    print(f"Relocating {templates.count()} job templates...")

    store_cache = {} # (pref, city) -> Store object

    for tmpl in templates:
        pref = tmpl.store.prefecture
        # ランダムにその県の都市を選択
        city_info = random.choice(DIVERSE_LOCATIONS[pref])
        city_name, lat, lng = city_info
        
        cache_key = (pref, city_name)
        if cache_key not in store_cache:
            store_name = f"{pref} {city_name.split('市')[0]}エリア店"
            store, created = Store.objects.get_or_create(
                business=biz_profile,
                prefecture=pref,
                city=city_name,
                defaults={
                    'store_name': store_name,
                    'post_code': "0000000",
                    'address_line': f"{random.randint(1, 15)}-{random.randint(1, 5)}",
                    'latitude': lat + random.uniform(-0.01, 0.01),
                    'longitude': lng + random.uniform(-0.01, 0.01),
                    'industry': tmpl.industry
                }
            )
            store_cache[cache_key] = store
        
        # テンプレートを新しい（またはランダムに選ばれた）店舗に紐付け直す
        new_store = store_cache[cache_key]
        tmpl.store = new_store
        tmpl.address = new_store.full_address
        tmpl.latitude = new_store.latitude
        tmpl.longitude = new_store.longitude
        tmpl.save()
        
        # 関連する求人投稿のタイトルも更新（もしあれば）
        JobPosting.objects.filter(template=tmpl).update(title=tmpl.title)

    print("Successfully distributed regional stores and templates.")

if __name__ == "__main__":
    distribute_stores()
