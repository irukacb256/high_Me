import os
import django
import random
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate

# 主要な都道府県の基準座標 (県庁所在地付近)
PREF_COORDS = {
    "東京都": (35.6895, 139.6917),
    "神奈川県": (35.4478, 139.6425),
    "埼玉県": (35.8617, 139.6455),
    "千葉県": (35.6073, 140.1233),
    "群馬県": (36.3895, 139.0634),
    "栃木県": (36.5658, 139.8836),
    "茨城県": (36.3659, 140.4714),
    "長野県": (36.6485, 138.1942),
    "山梨県": (35.6663, 138.5683),
    "静岡県": (34.9756, 138.3828),
    "愛知県": (35.1815, 136.9066),
    "大阪府": (34.6863, 135.5200),
    "京都府": (35.0210, 135.7556),
    "兵庫県": (34.6913, 135.1830),
    "福岡県": (33.6064, 130.4182),
    "北海道": (43.0642, 141.3468),
    "宮城県": (38.2682, 140.8694),
}

# デフォルト (日本中心付近)
DEFAULT_COORD = (35.0, 135.0)

def update_all_locations():
    print("Updating Store locations...")
    stores = Store.objects.all()
    store_updated = 0
    for store in stores:
        # 都道府県名を取得 (余計な空白などを除去)
        pref = store.prefecture.strip() if store.prefecture else ""
        base_lat, base_lng = PREF_COORDS.get(pref, DEFAULT_COORD)
        
        # 座標が未設定、またはすべて同じ座標（大宮など）に固まっている場合に更新
        # ユーザーが明示的に大宮を設定している可能性もあるが、今回は「全体反映」優先
        # 常に更新するか判定
        
        # ランダムに少しずらす (約3~5km圏内)
        lat_offset = random.uniform(-0.04, 0.04)
        lng_offset = random.uniform(-0.04, 0.04)
        
        store.latitude = base_lat + lat_offset
        store.longitude = base_lng + lng_offset
        store.save()
        store_updated += 1
        # print(f"  Updated Store: {store.store_name} ({pref})")

    print(f"Finished updating {store_updated} Stores.")

    print("\nUpdating JobTemplate locations...")
    templates = JobTemplate.objects.all()
    template_updated = 0
    for tmpl in templates:
        # ひな形に座標が設定されていない場合のみ、店舗の座標をコピー
        # あるいは今回一括で店舗基準にする
        if tmpl.latitude is None or tmpl.longitude is None:
            tmpl.latitude = tmpl.store.latitude
            tmpl.longitude = tmpl.store.longitude
            tmpl.save()
            template_updated += 1
        elif tmpl.latitude == 35.9063: # 旧スクリプトの固定値
            tmpl.latitude = tmpl.store.latitude
            tmpl.longitude = tmpl.store.longitude
            tmpl.save()
            template_updated += 1

    print(f"Finished updating {template_updated} JobTemplates.")

if __name__ == "__main__":
    update_all_locations()
