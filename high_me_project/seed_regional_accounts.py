import os
import django
import sys
from django.db import transaction

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile, Store

# 都道府県名とメールアドレスのプレフィックスのマップ
# ※表記ゆれ(英語名)にも対応できるよう、リスト形式でキーを持つか、正規化して処理
REGIONS = {
    'ibaraki': ['茨城県', 'Ibaraki'],
    'gunma': ['群馬県', 'Gunma'],
    'tochigi': ['栃木県', '栃木県', 'Tochigi'],
    'saitama': ['埼玉県', 'Saitama'],
    'chiba': ['千葉県', 'Chiba'],
    'tokyo': ['東京都', 'Tokyo'],
    'kanagawa': ['神奈川県', 'Kanagawa'],
    'yamanashi': ['山梨県', 'Yamanashi'],
    'nagano': ['長野県', 'Nagano'],
    'shizuoka': ['静岡県', 'Shizuoka'],
}

def migrate():
    print("Start regional account expansion and data migration...")
    
    password = "password123" # 開発用固定パスワード

    with transaction.atomic():
        for prefix, prefs in REGIONS.items():
            email = f"{prefix}@example.com"
            company_name = f"{prefs[0]}事業所"
            
            # 1. ユーザー作成
            user, created = User.objects.get_or_create(
                username=prefix,
                defaults={
                    'email': email,
                    'is_staff': False,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                print(f"Created user: {prefix} ({email})")
            
            # 2. 事業所プロフィール作成
            profile, p_created = BusinessProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': company_name,
                    'business_type': '法人',
                    'industry': 'その他',
                    'is_verified': True,
                    'prefecture': prefs[0]
                }
            )
            if p_created:
                print(f"Created BusinessProfile for {company_name}")

            # 3. 店舗の移行
            updated_count = Store.objects.filter(prefecture__in=prefs).update(business=profile)
            print(f"Moved {updated_count} stores to {company_name}")

    # 結果確認
    print("\nFinal Results (Stores per Business):")
    for bp in BusinessProfile.objects.all():
        count = bp.store_set.count()
        print(f"Business: {bp.company_name} ({bp.user.email}) -> {count} stores")

if __name__ == "__main__":
    migrate()
