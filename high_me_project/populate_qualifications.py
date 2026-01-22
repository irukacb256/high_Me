import os
import django

# Djangoの設定を読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import QualificationMaster

def populate():
    data = [
        # 運転免許
        ('普通自動車免許', '運転免許'),
        ('中型自動車免許', '運転免許'),
        ('大型自動車免許', '運転免許'),
        ('準中型自動車免許', '運転免許'),
        ('普通自動二輪車免許', '運転免許'),
        ('大型自動二輪車免許', '運転免許'),
        ('原付免許', '運転免許'),
        # 専門・技能
        ('フォークリフト', '専門・技能'),
        ('危険物取扱者（乙4）', '専門・技能'),
        ('食品衛生責任者', '専門・技能'),
        ('調理師', '専門・技能'),
        # 医療・介護
        ('介護職員初任者研修', '医療・介護'),
        ('登録販売者', '医療・介護'),
        # その他
        ('警備員新任教育受講済', 'その他'),
        ('衛生管理者', 'その他'),
    ]

    for name, category in data:
        obj, created = QualificationMaster.objects.get_or_create(name=name, category=category)
        if created:
            print(f"Created: {obj}")
        else:
            print(f"Already exists: {obj}")

if __name__ == '__main__':
    populate()
