import os
import django
import random
import sys
from datetime import timedelta, date, time

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, BusinessProfile
from django.utils import timezone

# 拡張された都市リスト
CITIES = {
    "群馬県": [
        ("高崎市", 36.3219, 139.0033), ("前橋市", 36.3895, 139.0634), 
        ("伊勢崎市", 36.3222, 139.1975), ("太田市", 36.2917, 139.3764),
        ("桐生市", 36.4167, 139.3333), ("館林市", 36.2458, 139.5417)
    ],
    "栃木県": [
        ("宇都宮市", 36.5658, 139.8836), ("小山市", 36.3147, 139.8003),
        ("足利市", 36.3333, 139.4500), ("栃木市", 36.3833, 139.7333),
        ("佐野市", 36.3167, 139.5833), ("鹿沼市", 36.5667, 139.7500)
    ],
    "茨城県": [
        ("水戸市", 36.3659, 140.4714), ("つくば市", 36.0835, 140.0764),
        ("日立市", 36.5917, 140.6500), ("土浦市", 36.0833, 140.2000),
        ("古河市", 36.1917, 139.7083), ("取手市", 35.8917, 140.0667)
    ],
    "東京都": [
        ("新宿区", 35.6895, 139.7004), ("渋谷区", 35.6580, 139.7016),
        ("豊島区", 35.7289, 139.7104), ("立川市", 35.6947, 139.4122),
        ("八王子市", 35.6556, 139.3367), ("町田市", 35.5467, 139.4464)
    ],
    "神奈川県": [
        ("横浜市中区", 35.4447, 139.6425), ("川崎市幸区", 35.5308, 139.6982),
        ("相模原市", 35.5714, 139.3736), ("藤沢市", 35.3389, 139.4894),
        ("厚木市", 35.4411, 139.3625), ("小田原市", 35.2556, 139.1594)
    ],
    "埼玉県": [
        ("さいたま市大宮区", 35.9067, 139.6267), ("川越市", 35.9250, 139.4858),
        ("所沢市", 35.7917, 139.4667), ("越谷市", 35.8903, 139.7903),
        ("熊谷市", 36.1472, 139.3886), ("川口市", 35.8083, 139.7194)
    ],
    "長野県": [
        ("長野市", 36.6485, 138.1942), ("松本市", 36.2378, 137.9719),
        ("上田市", 36.4000, 138.2500), ("岡谷市", 36.0583, 138.0417)
    ],
    "山梨県": [
        ("甲府市", 35.6663, 138.5683), ("富士吉田市", 35.4872, 138.8044),
        ("笛吹市", 35.6500, 138.6333)
    ],
    "静岡県": [
        ("静岡市", 34.9756, 138.3828), ("浜松市", 34.7038, 137.7348),
        ("沼津市", 35.1017, 138.8597), ("富士市", 35.1500, 138.6833)
    ]
}

JOB_TITLES = [
    "【{city}】カフェスタッフ急募！", "駅チカ！イベント設営アシスタント", "オープニング！商品陳列・品出し",
    "【高時給】デリバリー配達員", "短期！倉庫内軽作業スタッフ", "ペットショップでの接客補助",
    "和食レストランのホールスタッフ", "アパレル販売応援スタッフ", "オフィスビル清掃・ゴミ回収",
    "ホテルの客室清掃・ベッドメイク", "【週1〜】チラシ配布ポスティング", "パン屋さんの製造補助"
]

OCCUPATIONS = ["飲食・フード", "イベント・レジャー", "販売・接客", "軽作業・製造", "清掃", "配達・ドライバー"]

def generate_mass_data():
    biz_profile = BusinessProfile.objects.first()
    if not biz_profile:
        print("Error: No BusinessProfile found.")
        return

    today = timezone.localdate()
    total_postings = 0

    print("Generating stores and job postings...")

    for pref, cities in CITIES.items():
        for city_item in cities:
            city_name, base_lat, base_lng = city_item
            
            # 各都市に1-3店舗作成
            num_stores = random.randint(1, 3)
            for i in range(num_stores):
                store_name = f"{city_name} {random.choice(['駅前', '中央', 'バイパス', 'イオンモール'])}店"
                industry = random.choice(["カフェ・喫茶店", "居酒屋", "物流倉庫", "スーパーマーケット", "ホテル"])
                
                store, created = Store.objects.get_or_create(
                    business=biz_profile,
                    store_name=store_name,
                    defaults={
                        'industry': industry,
                        'post_code': f"{random.randint(100, 999)}{random.randint(1000, 9999)}",
                        'prefecture': pref,
                        'city': city_name,
                        'address_line': f"{random.randint(1, 20)}-{random.randint(1, 10)}",
                        'latitude': base_lat + random.uniform(-0.02, 0.02),
                        'longitude': base_lng + random.uniform(-0.02, 0.02),
                    }
                )

                # 各店舗に1-2件のテンプレート作成
                num_templates = random.randint(1, 2)
                for j in range(num_templates):
                    title = random.choice(JOB_TITLES).format(city=city_name)
                    tmpl, t_created = JobTemplate.objects.get_or_create(
                        store=store,
                        title=title,
                        defaults={
                            'industry': industry,
                            'occupation': random.choice(OCCUPATIONS),
                            'work_content': "未経験から始められる簡単なお仕事です。先輩が丁寧に教えます。",
                            'precautions': "清潔感のある服装でお願いします。時間に余裕を持って集合してください。",
                            'address': store.full_address,
                            'latitude': store.latitude,
                            'longitude': store.longitude,
                            'contact_number': "09012345678"
                        }
                    )

                    # 向こう14日間のうちランダムに3-8日分の投稿作成
                    num_days = random.randint(3, 8)
                    sample_days = random.sample(range(14), num_days)
                    for day_offset in sample_days:
                        work_date = today + timedelta(days=day_offset)
                        start_h = random.randint(8, 18)
                        start_time = time(start_h, random.choice([0, 30]))
                        end_time = time((start_h + random.randint(3, 8)) % 24, random.choice([0, 30]))
                        
                        JobPosting.objects.create(
                            template=tmpl,
                            work_date=work_date,
                            start_time=start_time,
                            end_time=end_time,
                            title=tmpl.title,
                            work_content=tmpl.work_content,
                            hourly_wage=random.choice([1100, 1200, 1300, 1500]),
                            recruitment_count=random.randint(1, 5),
                            visibility='public',
                            is_published=True
                        )
                        total_postings += 1

    print(f"Successfully generated {total_postings} job postings across regional cities.")

if __name__ == "__main__":
    generate_mass_data()
