import os
import django
import random
import sys
from datetime import timedelta, date, time, datetime

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, BusinessProfile
from django.utils import timezone
from django.contrib.auth.models import User

# 都県ごとの市区町村リストと基準座標
MUNICIPALITIES = {
    "茨城県": {
        "user": "ibaraki",
        "base_lat": 36.3659, "base_lng": 140.4714, # 水戸
        "cities": ["水戸市", "日立市", "土浦市", "古河市", "石岡市", "結城市", "龍ケ崎市", "下妻市", "常総市", "常陸太田市", "高萩市", "北茨城市", "笠間市", "取手市", "牛久市", "つくば市", "ひたちなか市", "鹿嶋市", "潮来市", "守谷市", "常陸大宮市", "那珂市", "筑西市", "坂東市", "稲敷市", "かすみがうら市", "桜川市", "神栖市", "行方市", "鉾田市", "つくばみらい市", "小美玉市", "茨城町", "大洗町", "城里町", "東海村", "大子町", "美浦村", "阿見町", "河内町", "八千代町", "五霞町", "境町", "利根町"]
    },
    "栃木県": {
        "user": "tochigi",
        "base_lat": 36.5658, "base_lng": 139.8836, # 宇都宮
        "cities": ["宇都宮市", "足利市", "栃木市", "佐野市", "鹿沼市", "日光市", "小山市", "真岡市", "大田原市", "矢板市", "那須塩原市", "さくら市", "那須烏山市", "下野市", "上三川町", "益子町", "茂木町", "市貝町", "芳賀町", "壬生町", "野木町", "塩谷町", "高根沢町", "那須町", "那珂川町"]
    },
    "群馬県": {
        "user": "gunma",
        "base_lat": 36.3895, "base_lng": 139.0634, # 前橋
        "cities": ["前橋市", "高崎市", "桐生市", "伊勢崎市", "太田市", "沼田市", "館林市", "渋川市", "藤岡市", "富岡市", "安中市", "みどり市", "榛東村", "吉岡町", "上野村", "神流町", "下仁田町", "南牧村", "甘楽町", "中之条町", "長野原町", "嬬恋村", "草津町", "高山村", "東吾妻町", "片品村", "川場村", "昭和村", "みなかみ町", "玉村町", "板倉町", "明和町", "千代田町", "大泉町", "邑楽町"]
    },
    "埼玉県": {
        "user": "saitama",
        "base_lat": 35.9067, "base_lng": 139.6267, # 大宮
        "cities": ["さいたま市", "川越市", "熊谷市", "川口市", "行田市", "秩父市", "所沢市", "飯能市", "加須市", "本庄市", "東松山市", "春日部市", "狭山市", "羽生市", "鴻巣市", "深谷市", "上尾市", "草加市", "越谷市", "蕨市", "戸田市", "入間市", "朝霞市", "志木市", "和光市", "新座市", "桶川市", "久喜市", "北本市", "八潮市", "富士見市", "三郷市", "蓮田市", "坂戸市", "幸手市", "鶴ヶ島市", "日高市", "吉川市", "ふじみ野市", "白岡市"]
    },
    "千葉県": {
        "user": "chiba",
        "base_lat": 35.6074, "base_lng": 140.1065, # 千葉
        "cities": ["千葉市", "銚子市", "市川市", "船橋市", "館山市", "木更津市", "松戸市", "野田市", "茂原市", "成田市", "佐倉市", "東金市", "旭市", "習志野市", "柏市", "勝浦市", "市原市", "流山市", "八千代市", "我孫子市", "鴨川市", "鎌ケ谷市", "君津市", "富津市", "浦安市", "四街道市", "袖ケ浦市", "八街市", "印西市", "白井市", "富里市", "南房総市", "匝瑳市", "香取市", "山武市", "いすみ市", "大網白里市"]
    },
    "東京都": {
        "user": "tokyo",
        "base_lat": 35.6895, "base_lng": 139.6917, # 新宿
        "cities": ["千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区", "江東区", "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区", "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区", "八王子市", "立川市", "武蔵野市", "三鷹市", "青梅市", "府中市", "昭島市", "調布市", "町田市", "小金井市", "小平市", "日野市", "東村山市", "国分寺市", "国立市", "福生市", "狛江市", "東大和市", "清瀬市", "東久留米市", "武蔵村山市", "多摩市", "稲城市", "羽村市", "あきる野市", "西東京市"]
    },
    "神奈川県": {
        "user": "kanagawa",
        "base_lat": 35.4475, "base_lng": 139.6425, # 横浜
        "cities": ["横浜市", "川崎市", "相模原市", "横須賀市", "平塚市", "鎌倉市", "藤沢市", "小田原市", "茅ヶ崎市", "逗子市", "三浦市", "秦野市", "厚木市", "大和市", "伊勢原市", "海老名市", "座間市", "南足柄市", "綾瀬市", "葉山町", "寒川町", "大磯町", "二宮町", "中井町", "大井町", "松田町", "山北町", "開成町", "箱根町", "真鶴町", "湯河原町", "愛川町", "清川村"]
    },
    "山梨県": {
        "user": "yamanashi",
        "base_lat": 35.6663, "base_lng": 138.5683, # 甲府
        "cities": ["甲府市", "富士吉田市", "都留市", "山梨市", "大月市", "韮崎市", "南アルプス市", "北杜市", "甲斐市", "笛吹市", "上野原市", "甲州市", "中央市", "市川三郷町", "早川町", "身延町", "南部町", "富士川町", "昭和町", "道志村", "西桂町", "忍野村", "山中湖村", "鳴沢村", "富士河口湖町", "小菅村", "丹波山村"]
    },
    "長野県": {
        "user": "nagano",
        "base_lat": 36.6485, "base_lng": 138.1942, # 長野
        "cities": ["長野市", "松本市", "上田市", "岡谷市", "飯田市", "諏訪市", "須坂市", "小諸市", "伊那市", "駒ヶ根市", "中野市", "大町市", "飯山市", "茅野市", "塩尻市", "佐久市", "千曲市", "東御市", "安曇野市", "軽井沢町", "御代田町", "立科町", "下諏訪町", "富士見町", "辰野町", "箕輪町", "飯島町", "松川町", "高森町", "阿南町", "上松町", "木曽町", "池田町", "坂城町", "小布施町", "山ノ内町", "信濃町", "飯綱町"]
    },
    "静岡県": {
        "user": "shizuoka",
        "base_lat": 34.9756, "base_lng": 138.3828, # 静岡
        "cities": ["静岡市", "浜松市", "沼津市", "熱海市", "三島市", "富士宮市", "伊東市", "島田市", "富士市", "磐田市", "焼津市", "掛川市", "藤枝市", "御殿場市", "袋井市", "下田市", "裾野市", "湖西市", "伊豆市", "御前崎市", "菊川市", "伊豆の国市", "牧之原市", "東伊豆町", "河津町", "南伊豆町", "松崎町", "西伊豆町", "函南町", "清水町", "長泉町", "小山町", "吉田町", "川根本町", "森町"]
    }
}

JOB_TITLES = [
    "【{city}】地域密着！店舗スタッフ", "【急募】{city}での短期軽作業", "{city}駅チカ！接客・販売",
    "【高時給】{city}デリバリー担当", "{city}内での施設清掃・整備", "{city}イベント運営アシスタント"
]

OCCUPATIONS = ["飲食・フード", "イベント・レジャー", "販売・接客", "軽作業・製造", "清掃", "配達・ドライバー"]

def seed_municipalities():
    print("Start comprehensive regional seeding...")
    today = timezone.localdate()
    total_stores = 0
    total_jobs = 0

    for pref_name, config in MUNICIPALITIES.items():
        print(f"Processing {pref_name}...")
        
        # 地域別ビジネスアカウントの取得
        try:
            user = User.objects.get(username=config['user'])
            biz_profile = user.businessprofile
        except (User.DoesNotExist, Exception) as e:
            print(f"  Warning: Regional user {config['user']} not found. Skipping {pref_name}.")
            continue

        for city in config['cities']:
            # 店舗の作成
            store_name = f"{city} 拠点事務所"
            lat = config['base_lat'] + random.uniform(-0.15, 0.15)
            lng = config['base_lng'] + random.uniform(-0.2, 0.2)
            
            # 特例: 東京23区や主要都市に近い場合は少し調整
            if "区" in city and pref_name == "東京都":
                lat = config['base_lat'] + random.uniform(-0.05, 0.05)
                lng = config['base_lng'] + random.uniform(-0.08, 0.08)

            store, created = Store.objects.get_or_create(
                business=biz_profile,
                store_name=store_name,
                defaults={
                    'industry': random.choice(["サービス", "流通", "飲食"]),
                    'post_code': "0000000",
                    'prefecture': pref_name,
                    'city': city,
                    'address_line': "1-1",
                    'latitude': lat,
                    'longitude': lng,
                }
            )
            if created:
                total_stores += 1
            
            # 求人ひな形の作成
            title = random.choice(JOB_TITLES).format(city=city)
            tmpl, t_created = JobTemplate.objects.get_or_create(
                store=store,
                title=title,
                defaults={
                    'industry': store.industry,
                    'occupation': random.choice(OCCUPATIONS),
                    'work_content': f"{city}エリアでの地域貢献を目的としたお仕事です。未経験の方でも安心して始められます。",
                    'precautions': "時間厳守でお願いします。",
                    'address': store.full_address,
                    'latitude': store.latitude,
                    'longitude': store.longitude,
                    'contact_number': "090-0000-0000"
                }
            )

            # 向こう14日間のうちランダムに2-4日分の投稿作成
            num_days = random.randint(2, 4)
            sample_days = random.sample(range(14), num_days)
            for day_offset in sample_days:
                work_date = today + timedelta(days=day_offset)
                start_h = random.randint(9, 16)
                
                JobPosting.objects.create(
                    template=tmpl,
                    work_date=work_date,
                    start_time=time(start_h, 0),
                    end_time=time((start_h + 4) % 24, 0),
                    title=tmpl.title,
                    hourly_wage=1100,
                    recruitment_count=random.randint(1, 3),
                    visibility='public',
                    is_published=True
                )
                total_jobs += 1

    print(f"\nSeeding Complete.")
    print(f"Total Stores Created/Updated: {total_stores}")
    print(f"Total Job Postings Created: {total_jobs}")

if __name__ == "__main__":
    seed_municipalities()
