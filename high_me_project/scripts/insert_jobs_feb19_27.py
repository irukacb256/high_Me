import os
import django
import random
from datetime import date, timedelta, datetime
import sys

# Django Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, JobTemplatePhoto
from django.utils import timezone

def insert_jobs():
    print("Starting job insertion for Feb 19 - Feb 27, 2026...")

    stores = list(Store.objects.all())
    if not stores:
        print("No stores found. Please create stores first.")
        return

    # Sample Data
    titles = [
        "【急募】ホールスタッフ", "キッチン補助募集", "簡単な品出し作業", 
        "イベント運営スタッフ", "カフェ店員募集", "清掃スタッフ募集", 
        "配送助手のお仕事", "事務アシスタント", "データ入力業務", "倉庫内軽作業"
    ]
    industries = ["飲食", "小売", "サービス", "流通", "イベント", "オフィス", "物流"]
    occupations = ["ホール", "キッチン", "品出し", "受付", "カフェ", "清掃", "軽作業", "事務", "データ入力", "梱包"]
    contents = [
        "接客業務、オーダー取り、配膳、レジ対応などをお願いします。",
        "簡単な盛り付け、食器洗浄、調理補助をお願いします。",
        "商品の陳列、棚出し、在庫確認などをお願いします。",
        "お客様のご案内、会場の設営・撤去作業をお願いします。",
        "コーヒーの提供、軽食の調理、清掃をお願いします。",
        "オフィスビルの清掃、ゴミ回収、床掃除などをお願いします。",
        "伝票整理、電話対応、簡単なデータ入力をお願いします。"
    ]
    auto_messages = [
        None,
        "ご応募ありがとうございます！当日は裏口から入店し、担当者をお呼びください。",
        "マッチングありがとうございます。不明点があればメッセージでお知らせください。",
        "よろしくお願いいたします。ユニフォームはお貸ししますので、動きやすい靴でお越しください。"
    ]
    
    # Existing images in media/job_templates/photos/
    # We will just pick random file names from the directory listing we saw earlier
    # Note: These paths should be relative to MEDIA_ROOT
    available_images = [
        "job_templates/photos/cafe_16_9_1770250722575.png",
        "job_templates/photos/kitchen_16_9_1770250736177.png",
        "job_templates/photos/warehouse_16_9_1770250751403.png",
        "job_templates/photos/event_16_9_1770250770297.png",
        "job_templates/photos/cafe_job_image_1770250453633.png",
        "job_templates/photos/kitchen_job_image_1770250469374.png",
        "job_templates/photos/warehouse_job_image_1770250485224.png",
        "job_templates/photos/event_staff_image_1770250498286.png",
    ]

    start_date = date(2026, 2, 19)
    end_date = date(2026, 2, 27)
    delta = timedelta(days=1)
    
    current_date = start_date
    total_created = 0

    while current_date <= end_date:
        # Create about 30 jobs per day
        daily_job_count = random.randint(28, 32)
        print(f"Creating {daily_job_count} jobs for {current_date}")

        for _ in range(daily_job_count):
            store = random.choice(stores)
            title = random.choice(titles)
            
            # Create Template
            template = JobTemplate.objects.create(
                store=store,
                title=f"{title} ({current_date.strftime('%m/%d')})",
                industry=random.choice(industries),
                occupation=random.choice(occupations),
                work_content=random.choice(contents),
                precautions="・遅刻厳禁です。\n・清潔感のある服装でお願いします。",
                belongings="・筆記用具\n・身分証明書",
                requirements="・未経験者歓迎\n・元気な方",
                address=store.full_address,
                contact_number="03-0000-0000",
                auto_message=random.choice(auto_messages),
                
                # Questions
                question1="飲食店の経験はありますか？" if random.choice([True, False]) else None,
                question2="当日の体調は万全ですか？" if random.choice([True, False]) else None,
                question3="緊急連絡先を教えてください。" if random.choice([True, False]) else None,

                # Benefits
                has_unexperienced_welcome=random.choice([True, False]),
                has_bike_car_commute=random.choice([True, False]),
                has_clothing_free=random.choice([True, False]),
                has_coupon_get=random.choice([True, False]),
                has_meal=random.choice([True, False]),
                has_hair_color_free=random.choice([True, False]),
                has_transportation_allowance=random.choice([True, False]),
                
                requires_qualification=False
            )
            
            # Assign Random Images to Template
            num_images = random.randint(1, 3)
            selected_images = random.sample(available_images, num_images)
            for i, img_path in enumerate(selected_images):
                JobTemplatePhoto.objects.create(
                    template=template,
                    image=img_path,
                    order=i
                )

            # Create Posting
            start_hour = random.randint(8, 18)
            duration = random.randint(3, 6)
            end_hour = (start_hour + duration) % 24
            
            start_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M").time()
            end_time = datetime.strptime(f"{end_hour:02d}:00", "%H:%M").time()
            
            # Deadline is usually the day before or same day
            deadline = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))

            JobPosting.objects.create(
                template=template,
                work_date=current_date,
                start_time=start_time,
                end_time=end_time,
                title=template.title,
                work_content=template.work_content,
                hourly_wage=random.choice([1100, 1200, 1300, 1500]),
                transportation_fee=random.choice([0, 500, 1000]),
                application_deadline=deadline,
                recruitment_count=random.randint(1, 4),
                visibility='public',
                is_published=True
            )
            total_created += 1

        current_date += delta

    print(f"Finished! Total jobs created: {total_created}")

if __name__ == "__main__":
    insert_jobs()
