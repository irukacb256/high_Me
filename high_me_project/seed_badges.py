import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Badge

badges_data = [
    {"name": "グッドワーカー", "description": "店舗からの評価が高いワーカーに贈られます。"},
    {"name": "遅刻ゼロ", "description": "過去10回のお仕事で遅刻がないワーカーに贈られます。"},
    {"name": "キャンセルゼロ", "description": "直前キャンセルを行っていない信頼できるワーカーに贈られます。"},
    {"name": "リピーター", "description": "同じ店舗で複数回勤務したワーカーに贈られます。"},
    {"name": "即戦力", "description": "初めての職場でも高いパフォーマンスを発揮したワーカーに贈られます。"},
    {"name": "コミュニケーション", "description": "挨拶や報告・連絡・相談がしっかりできるワーカーに贈られます。"},
]

created_count = 0
for data in badges_data:
    badge, created = Badge.objects.get_or_create(name=data["name"], defaults={"description": data["description"]})
    if created:
        print(f"Created badge: {badge.name}")
        created_count += 1
    else:
        print(f"Badge already exists: {badge.name}")

print(f"Total new badges created: {created_count}")
