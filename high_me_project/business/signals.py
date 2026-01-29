from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Store
import requests

@receiver(pre_save, sender=Store)
def geocode_store_address(sender, instance, **kwargs):
    # 住所が変更された場合のみ実行 (または新規作成時)
    if instance.pk:
        try:
            old_instance = Store.objects.get(pk=instance.pk)
            old_address = f"{old_instance.prefecture}{old_instance.city}{old_instance.address_line}"
            new_address = f"{instance.prefecture}{instance.city}{instance.address_line}"
            if old_address == new_address and instance.latitude is not None:
                return
        except Store.DoesNotExist:
            pass # 新規作成扱い

    # 住所結合
    address = f"{instance.prefecture}{instance.city}{instance.address_line}"
    
    headers = {
        'User-Agent': 'HighMeApp/1.0 (contact@example.com)'
    }
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        # タイムアウトを設定して同期処理ブロックを緩和
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data:
            instance.latitude = float(data[0]['lat'])
            instance.longitude = float(data[0]['lon'])
            
    except Exception as e:
        # エラー時は更新しない (ログ出力などを検討)
        print(f"Geocoding error: {e}")
