import os
import django
import sys
import random

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobTemplate, JobTemplatePhoto

# カテゴリ別イメージ画像 (media内パス)
IMAGE_MAP = {
    'cafe': 'job_templates/photos/cafe_job_image_1770250453633.png',
    'kitchen': 'job_templates/photos/kitchen_job_image_1770250469374.png',
    'warehouse': 'job_templates/photos/warehouse_job_image_1770250485224.png',
    'event': 'job_templates/photos/event_staff_image_1770250498286.png',
}

def add_images():
    print("Start adding images to regional job templates...")
    
    # 画像がないすべてのひな形を対象にする
    templates = JobTemplate.objects.filter(photos__isnull=True)
    
    added_count = 0
    for t in templates:
        # すでに画像がある場合はスキップ
        if t.photos.exists():
            continue
            
        # 職種やタイトルから画像を推測
        occ = t.occupation or ""
        ind = t.industry or ""
        title = t.title or ""
        
        target_img = None
        if any(kw in occ or kw in title for kw in ['カフェ', '接客', 'ホール', '販売']):
            target_img = IMAGE_MAP['cafe']
        elif any(kw in occ or kw in title for kw in ['キッチン', '調理', '洗い場', '飲食']):
            target_img = IMAGE_MAP['kitchen']
        elif any(kw in occ or kw in title for kw in ['倉庫', '物流', '軽作業', '搬入', 'ピッキング']):
            target_img = IMAGE_MAP['warehouse']
        elif any(kw in occ or kw in title for kw in ['イベント', '設営', '案内']):
            target_img = IMAGE_MAP['event']
        else:
            # デフォルトはランダム
            target_img = random.choice(list(IMAGE_MAP.values()))
            
        # 写真を追加
        JobTemplatePhoto.objects.create(
            template=t,
            image=target_img,
            order=0
        )
        added_count += 1
        print(f"Added photo to: {t.title} ({t.store.prefecture})")

    print(f"Job image assignment completed. Total images added: {added_count}")

if __name__ == "__main__":
    add_images()
