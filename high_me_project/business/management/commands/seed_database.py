from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from business.models import BusinessProfile, Store, JobTemplate, JobPosting, JobTemplatePhoto
from accounts.models import WorkerProfile
import random
from datetime import timedelta, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import time

class Command(BaseCommand):
    help = 'Recreate database with realistic sample data'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")
        
        # Cleanup
        self.stdout.write("Deleting old data...")
        JobPosting.objects.all().delete()
        JobTemplate.objects.all().delete()
        Store.objects.all().delete()
        BusinessProfile.objects.all().delete()
        # Note: Keeping Users to avoid admin deletion/login issues for now, 
        # or we could strictly filter. Let's create a fresh business user.
        
        # Real Addresses Data
        # 千葉、東京、神奈川、埼玉のデータ
        real_stores = [
            # 千葉県
            {"name": "海浜幕張カフェ", "pref": "千葉県", "city": "千葉市美浜区", "addr": "ひび野2-110", "type": "カフェ", "color": (255, 200, 200)},
            {"name": "船橋ラーメン道場", "pref": "千葉県", "city": "船橋市", "addr": "本町7-1-1", "type": "ラーメン", "color": (200, 255, 200)},
            {"name": "柏ステーションコンビニ", "pref": "千葉県", "city": "柏市", "addr": "末広町1-1", "type": "コンビニ", "color": (200, 200, 255)},
            # 東京都
            {"name": "渋谷スカイダイニング", "pref": "東京都", "city": "渋谷区", "addr": "渋谷2-24-12", "type": "レストラン", "color": (255, 255, 200)},
            {"name": "新宿西口居酒屋", "pref": "東京都", "city": "新宿区", "addr": "西新宿1-1-3", "type": "居酒屋", "color": (200, 255, 255)},
            {"name": "東京駅丸の内書店", "pref": "東京都", "city": "千代田区", "addr": "丸の内1-9-1", "type": "小売店", "color": (255, 200, 255)},
            # 神奈川県
            {"name": "横浜中華街飯店", "pref": "神奈川県", "city": "横浜市中区", "addr": "山下町118-2", "type": "中華", "color": (255, 150, 150)},
            {"name": "川崎駅前カフェ", "pref": "神奈川県", "city": "川崎市川崎区", "addr": "駅前本町26-1", "type": "カフェ", "color": (150, 255, 150)},
            {"name": "江ノ島シーサイド", "pref": "神奈川県", "city": "藤沢市", "addr": "江の島1-3-2", "type": "レストラン", "color": (150, 150, 255)},
            # 埼玉県
            {"name": "大宮ソニックイベント", "pref": "埼玉県", "city": "さいたま市大宮区", "addr": "桜木町1-7-5", "type": "イベント", "color": (255, 255, 150)},
        ]

        # Create Business User
        user, created = User.objects.get_or_create(username='sample_biz', defaults={'email': 'biz@example.com'})
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write("Created user: sample_biz")

        # Create Business Profile
        biz_profile, _ = BusinessProfile.objects.get_or_create(
            user=user,
            defaults={
                'company_name': '株式会社サンプル興業',
                'business_type': '飲食・小売',
                'industry': 'サービス業',
                'prefecture': '東京都',
                'city': '港区',
                'address_line': '六本木1-1-1'
            }
        )

        # Helper to generate image
        def generate_image(color, text):
            img = Image.new('RGB', (600, 400), color=color)
            draw = ImageDraw.Draw(img)
            # 簡易的な描画
            draw.rectangle([50, 50, 550, 350], outline="white", width=5)
            # 文字入れたいけどフォントパス必要なので省略、枠線だけ
            f = io.BytesIO()
            img.save(f, format='JPEG')
            return ContentFile(f.getvalue(), name=f"{text}.jpg")

        today = timezone.localdate()

        for store_data in real_stores:
            self.stdout.write(f"Creating store: {store_data['name']}...")
            
            # Create Store (Signal will trigger geocoding)
            store = Store.objects.create(
                business=biz_profile,
                store_name=store_data['name'],
                industry=store_data['type'],
                post_code="000-0000", # Dummy
                prefecture=store_data['pref'],
                city=store_data['city'],
                address_line=store_data['addr'],
                building=""
            )
            
            # Request wait for Geocoding API limit
            time.sleep(2.0)
            
            # Create Job Template
            template = JobTemplate.objects.create(
                store=store,
                title=f"【{store_data['name']}】オープニングスタッフ募集！",
                industry=store_data['type'],
                occupation="ホール・キッチン",
                work_content="お客様のご案内、オーダー、料理の提供などをお願いします。",
                precautions="動きやすい服装でお願いします。",
                has_unexperienced_welcome=True,
                has_meal=True,
                has_transportation_allowance=True
            )
            
            # Basic Image
            photo_file = generate_image(store_data['color'], store_data['name'])
            JobTemplatePhoto.objects.create(template=template, image=photo_file, order=1)

            # Create Job Postings (Various dates)
            for i in range(3):
                date_offset = random.randint(0, 14) # Within 2 weeks
                job_date = today + timedelta(days=date_offset)
                
                start_h = random.choice([9, 10, 17, 18])
                end_h = start_h + random.choice([4, 5]) # Up to 23 Max
                
                JobPosting.objects.create(
                    template=template,
                    visibility='public',
                    work_date=job_date,
                    start_time=datetime.strptime(f"{start_h}:00", "%H:%M").time(),
                    end_time=datetime.strptime(f"{end_h}:00", "%H:%M").time(),
                    hourly_wage=random.choice([1100, 1200, 1300, 1500]),
                    # vacancy_count is actually recruitment_count in model?
                    recruitment_count=3
                )
        
        self.stdout.write(self.style.SUCCESS("Successfully seeded database with real addresses and coordinates."))
