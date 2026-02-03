import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Badge

badges_data = [
    {"name": "ホール", "description": "飲食店での接客、配膳、片付け、会計などの業務"},
    {"name": "洗い場", "description": "飲食店、ホテルでの食器・調理器具の洗浄や片付け"},
    {"name": "調理", "description": "飲食店、ホテル、スーパーでの食材の調理、仕込み、盛り付けなど"},
    {"name": "品出し", "description": "スーパー、コンビニ、ドラッグストアなどでの商品補充や陳列、値下げシール貼り"},
    {"name": "清掃", "description": "ホテル、スーパー、コンビニの清掃作業"},
    {"name": "レジ", "description": "スーパーやコンビニでのレジ業務、袋詰めやお客様誘導"},
    {"name": "検品", "description": "倉庫や工場での商品の傷や破損チェック、梱包状態の確認"},
    {"name": "仕分け", "description": "倉庫や工場での荷物分類、特定場所への運搬"},
    {"name": "ピッキング", "description": "倉庫で注文書をもとに必要な品物を集める作業"},
    {"name": "梱包", "description": "倉庫で商品を指定方法で包装する作業"},
    {"name": "搬入出", "description": "販売店舗やイベント会場への資材搬入・搬出"},
    {"name": "フロント", "description": "ホテルや企業受付、チェックイン・チェックアウト・問い合わせ対応"},
    {"name": "宴会スタッフ", "description": "ホテルでの宴会運営補助、料理や飲み物の提供、設営・撤去"},
    {"name": "配達", "description": "フードデリバリーや送迎業務"},
]

print("Deleting existing badges...")
Badge.objects.all().delete()
print("Existing badges deleted.")

created_count = 0
for data in badges_data:
    badge, created = Badge.objects.get_or_create(name=data["name"])
    if created:
        badge.description = data["description"]
        badge.save()
        print(f"Created badge: {badge.name}")
        created_count += 1
    else:
        print(f"Badge already exists: {badge.name}")
        # Update description just in case
        badge.description = data["description"]
        badge.save()

print(f"Total badges created: {created_count}")
