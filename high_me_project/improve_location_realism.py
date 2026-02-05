import os
import django
import random
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate

# より詳細な地域データ
REAL_LOCATIONS = {
    "東京都": [
        ("新宿区新宿", 35.6938, 139.7034, "新宿テラスカフェ"),
        ("港区芝公園", 35.6586, 139.7454, "芝公園ベーカリー"),
        ("豊島区東池袋", 35.7295, 139.7186, "池袋サンシャイン店"),
        ("世田谷区下北沢", 35.6620, 139.6672, "下北沢ビンテージカフェ")
    ],
    "神奈川県": [
        ("横浜市西区みなとみらい", 35.4578, 139.6325, "みなとみらいダイナー"),
        ("鎌倉市小町", 35.3192, 139.5467, "鎌倉小町通りレストラン"),
        ("藤沢市片瀬海岸", 35.3088, 139.4811, "江ノ島サーフサイド"),
        ("川崎市中原区", 35.5756, 139.6586, "武蔵小杉フードコート")
    ],
    "埼玉県": [
        ("さいたま市大宮区桜木町", 35.9063, 139.6240, "大宮駅前マーケット"),
        ("川越市脇田町", 35.9073, 139.4833, "小江戸川越横丁"),
        ("所沢市くすのき台", 35.7876, 139.4735, "所沢パークショップ"),
        ("越谷市レイクタウン", 35.8789, 139.8273, "レイクタウンブティック")
    ],
    "群馬県": [
        ("高崎市八島町", 36.3219, 139.0033, "高崎駅前ステーション店"),
        ("前橋市本町", 36.3895, 139.0634, "前橋セントラルキッチン")
    ],
    "栃木県": [
        ("宇都宮市馬場通り", 36.5658, 139.8836, "宇都宮餃子テラス"),
        ("小山市中央町", 36.3147, 139.8003, "小山ステーションマート")
    ],
    "茨城県": [
        ("水戸市宮町", 36.3659, 140.4714, "水戸偕楽園ショップ"),
        ("つくば市吾妻", 36.0835, 140.0764, "つくばサイエンスカフェ")
    ],
    "長野県": [
        ("長野市南長野", 36.6485, 138.1942, "善光寺参道ベーカリー"),
        ("松本市中央", 36.2378, 137.9719, "松本城下町レストラン")
    ],
    "山梨県": [
        ("甲府市丸の内", 35.6663, 138.5683, "甲府城跡カフェ"),
        ("富士吉田市上吉田", 35.4872, 138.8044, "富士急ハイランド横ショップ")
    ],
    "静岡県": [
        ("静岡市葵区黒金町", 34.9756, 138.3828, "静岡おでん横丁店"),
        ("浜松市中区砂山町", 34.7038, 137.7348, "浜松餃子スタジアム")
    ]
}

def improve_realism():
    print("Improving Store and JobTemplate realism...")
    stores = Store.objects.all()
    updated_count = 0

    for store in stores:
        pref = store.prefecture.strip() if store.prefecture else ""
        if pref in REAL_LOCATIONS:
            # 地域に合わせたリアルなデータをランダムに選択
            choices = REAL_LOCATIONS[pref]
            city_addr, lat, lng, name_prefix = random.choice(choices)
            
            # 店舗名に個性を出す（既存の名前がテストっぽい場合）
            if "拠点店" in store.store_name or "総合拠点" in store.store_name or "Dummy" in store.store_name:
                store.store_name = f"{name_prefix}"
            
            # 住所更新
            store.city = city_addr
            store.address_line = f"{random.randint(1, 20)}-{random.randint(1, 10)}"
            
            # 精密座標 (微調整)
            store.latitude = lat + random.uniform(-0.005, 0.005)
            store.longitude = lng + random.uniform(-0.005, 0.005)
            store.save()
            
            # 紐付く JobTemplate も更新
            templates = JobTemplate.objects.filter(store=store)
            for tmpl in templates:
                tmpl.address = store.full_address
                tmpl.latitude = store.latitude
                tmpl.longitude = store.longitude
                
                # タイトルも地域名を入れるとリアル
                if pref in tmpl.title:
                    pass # 既に入っている
                else:
                    tmpl.title = f"【{pref}】{tmpl.title}"
                
                tmpl.save()
            
            updated_count += 1
            print(f"  Updated: {store.store_name} ({pref} {store.city})")

    print(f"\nSuccessfully improved realism for {updated_count} stores.")

if __name__ == "__main__":
    improve_realism()
