import os
import django
import sys
import shutil

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobTemplate, JobTemplatePhoto
from django.core.files import File

def apply_images():
    # Source paths (adjust based on generated paths)
    image_map = {
        "cafe": r"C:/Users/y_ootani/.gemini/antigravity/brain/c2045e4b-2b33-437e-9dff-95194b7a8edb/cafe_16_9_1770250722575.png",
        "kitchen": r"C:/Users/y_ootani/.gemini/antigravity/brain/c2045e4b-2b33-437e-9dff-95194b7a8edb/kitchen_16_9_1770250736177.png",
        "warehouse": r"C:/Users/y_ootani/.gemini/antigravity/brain/c2045e4b-2b33-437e-9dff-95194b7a8edb/warehouse_16_9_1770250751403.png",
        "event": r"C:/Users/y_ootani/.gemini/antigravity/brain/c2045e4b-2b33-437e-9dff-95194b7a8edb/event_16_9_1770250770297.png"
    }

    templates = JobTemplate.objects.all()
    print(f"Applying images to {templates.count()} templates...")

    for template in templates:
        # Overwrite existing photos
        template.photos.all().delete()
            
        title = template.title.lower()
        occupation = template.occupation.lower()
        
        target_key = "cafe" # default
        if "キッチン" in title or "kitchen" in title or "調理" in title:
            target_key = "kitchen"
        elif "品出し" in title or "配送" in title or "倉庫" in title:
            target_key = "warehouse"
        elif "イベント" in title or "受付" in title:
            target_key = "event"
        elif "カフェ" in title or "cafe" in title or "ホール" in title:
            target_key = "cafe"

        image_path = image_map.get(target_key)
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                photo = JobTemplatePhoto(template=template, order=0)
                photo.image.save(os.path.basename(image_path), File(f), save=True)
            print(f"Applied {target_key} image to: {template.title}")

    print("Finished applying images.")

if __name__ == "__main__":
    apply_images()
