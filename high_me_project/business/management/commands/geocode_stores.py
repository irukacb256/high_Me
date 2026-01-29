from django.core.management.base import BaseCommand
from business.models import Store
import requests
import time

class Command(BaseCommand):
    help = 'Geocode stores using Nominatim API'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force update all stores')

    def handle(self, *args, **options):
        if options['force']:
            stores = Store.objects.all()
        else:
            stores = Store.objects.filter(latitude__isnull=True)
            
        self.stdout.write(f"Found {stores.count()} stores to process.")
        
        headers = {
            'User-Agent': 'HighMeApp/1.0 (contact@example.com)'
        }
        
        for store in stores:
            # 住所結合: 都道府県 + 市区町村 + 番地 (建物名は精度落ちる可能性あるので一旦除くか、あるいは含めるか)
            # Nominatimは構造化クエリも投げられるが、qパラメータで投げたほうが柔軟な場合もある
            address = f"{store.prefecture}{store.city}{store.address_line}"
            
            try:
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': address,
                    'format': 'json',
                    'limit': 1
                }
                
                response = requests.get(url, params=params, headers=headers)
                data = response.json()
                
                if data:
                    lat = data[0]['lat']
                    lon = data[0]['lon']
                    store.latitude = float(lat)
                    store.longitude = float(lon)
                    store.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated {store.store_name}: {lat}, {lon}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Not found: {address}"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {store.store_name}: {str(e)}"))
            
            # Rate limit respect (1 second)
            time.sleep(1.0)
