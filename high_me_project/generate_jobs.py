import os
import django
import random
from datetime import date, timedelta, datetime
import sys

# Djangoのセットアップ
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobTemplate, JobPosting, JobTemplatePhoto
from django.core.files import File
from django.utils import timezone

def generate():
    stores = list(Store.objects.all())
    if not stores:
        print("店舗が見つかりません。店舗を先に作成してください。")
        return

    # サンプルデータ
    titles = ["【急募】ホールスタッフ", "キッチン補助募集", "簡単な品出し作業", "イベント運営スタッフ", "カフェ店員募集", "清掃スタッフ募集", "配送助手のお仕事"]
    industries = ["飲食", "小売", "サービス", "流通", "イベント"]
    occupations = ["ホール", "キッチン", "品出し", "受付", "カフェ", "清掃", "軽作業"]
    contents = [
        "接客業務、オーダー取り、配膳、レジ対応などをお願いします。",
        "簡単な盛り付け、食器洗浄、調理補助をお願いします。",
        "商品の陳列、棚出し、在庫確認などをお願いします。",
        "お客様のご案内、会場の設営・撤去作業をお願いします。",
        "コーヒーの提供、軽食の調理、清掃をお願いします。"
    ]
    precautions = "・遅刻厳禁です。\n・派手なネイル、髪色は不可です。\n・清潔感のある服装でお願いします。"
    belongings = "・印鑑\n・メモ帳、筆記用具\n・動きやすい靴"
    auto_messages = [
        None,
        "ご応募ありがとうございます！当日は裏口から入店し、店長をお呼びください。",
        "マッチングありがとうございます。不明点があればメッセージでお知らせください。",
        "よろしくお願いいたします。ユニフォームはお貸しします。"
    ]

    total_jobs = 100
    today = date.today()
    # 2月15日までの日数を計算して、1日4件ずつになるように調整
    target_date = date(2026, 2, 15)
    
    current_date = today
    count = 0
    
    # ダミーPDFと画像のパス（存在する場合）
    # 今回は簡易的にパスのみ設定（実際にファイルが必要な場合は別途用意が必要）
    
    print(f"Starting job generation: {total_jobs} jobs...")

    while count < total_jobs:
        # 1日4件ずつ作成
        for _ in range(4):
            if count >= total_jobs:
                break
                
            store = random.choice(stores)
            title = random.choice(titles)
            
            # テンプレートの作成
            template = JobTemplate.objects.create(
                store=store,
                title=f"{title} ({count+1})",
                industry=random.choice(industries),
                occupation=random.choice(occupations),
                work_content=random.choice(contents),
                precautions=precautions,
                belongings=belongings,
                requirements="・指示をしっかり聞ける方\n・明るく元気に接客できる方",
                address=store.full_address,
                contact_number="03-1234-5678",
                auto_message=random.choice(auto_messages),
                # 質問有り無しをランダムに
                question1="飲食店の経験はありますか？" if random.random() > 0.5 else None,
                question2="当日の体調は万全ですか？" if random.random() > 0.7 else None,
            )

            # 求人投稿の作成
            start_hour = random.randint(9, 15)
            duration = random.randint(3, 8)
            start_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M").time()
            end_time = datetime.strptime(f"{(start_hour+duration):02d}:00", "%H:%M").time()
            
            # 応募締切は勤務日の前日
            deadline = timezone.make_aware(datetime.combine(current_date - timedelta(days=1), datetime.min.time()))

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
                recruitment_count=random.randint(1, 5)
            )
            count += 1
            
        current_date += timedelta(days=1)
        if current_date > target_date:
            current_date = today # ループして日付を埋める

    print(f"Finished! Created {count} jobs.")

if __name__ == "__main__":
    generate()
