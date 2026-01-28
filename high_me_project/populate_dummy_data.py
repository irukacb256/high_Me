import os
import django
import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobPosting, JobTemplate, BusinessProfile, Store
from django.contrib.auth.models import User

def populate_data():
    print("--- Populating Dummy Data ---")

    # Business Owners Data
    businesses = [
        {
            'username': 'biz_chiba', 'company': 'Chiba Logistics Co.', 'type': 'Logistics',
            'stores': [
                {'name': 'Funabashi Warehouse', 'pref': '千葉県', 'city': 'Funabashi', 'post': '2730001'}
            ]
        },
        {
            'username': 'biz_saitama', 'company': 'Saitama Cafe Group', 'type': 'Restaurant',
            'stores': [
                {'name': 'Omiya Cafe Terrace', 'pref': '埼玉県', 'city': 'Saitama', 'post': '3300001'}
            ]
        },
        {
            'username': 'biz_kanagawa', 'company': 'Yokohama Events Inc.', 'type': 'Event',
            'stores': [
                {'name': 'Yokohama Arena Staff', 'pref': '神奈川県', 'city': 'Yokohama', 'post': '2220001'}
            ]
        }
    ]

    try:
        today = timezone.localdate()

        for biz_data in businesses:
            # Create User
            u, _ = User.objects.get_or_create(username=biz_data['username'])
            u.set_password('password')
            u.save()
            print(f"User: {u.username}")

            # Create BusinessProfile
            biz, _ = BusinessProfile.objects.get_or_create(user=u, defaults={
                'company_name': biz_data['company'],
                'business_type': biz_data['type']
            })

            for store_data in biz_data['stores']:
                # Create Store
                store, created = Store.objects.get_or_create(business=biz, store_name=store_data['name'], defaults={
                    'post_code': store_data['post'],
                    'prefecture': store_data['pref'],
                    'city': store_data['city'],
                    'address_line': '1-1-1',
                    'industry': biz_data['type']
                })
                
                # Create Template
                template, _ = JobTemplate.objects.get_or_create(store=store, title=f"{store_data['name']} Staff", defaults={
                    'industry': biz_data['type'],
                    'occupation': 'General Staff',
                    'work_content': 'General duties including customer service and cleaning.',
                    'precautions': 'Wear comfortable clothes.',
                    'address': f"{store_data['pref']} {store_data['city']} 1-1-1",
                    'contact_number': '03-0000-0000',
                    'has_unexperienced_welcome': True,
                    'has_transportation_allowance': True
                })

                # Create 3 Job Postings for each store
                start_hour_base = 9
                for i in range(3):
                    job_date = today + timedelta(days=i) # Today, Tomorrow, Day after
                    
                    # Varing start times
                    start_time = datetime.strptime(f"{start_hour_base + i}:00", '%H:%M').time()
                    end_time = datetime.strptime(f"{start_hour_base + i + 5}:00", '%H:%M').time() # 5 hours shift

                    JobPosting.objects.get_or_create(
                        template=template,
                        work_date=job_date,
                        start_time=start_time,
                        end_time=end_time,
                        defaults={
                            'title': f"{store_data['pref']} - {store_data['name']} Job {i+1}",
                            'work_content': f"Shift {i+1}: {store_data['name']} operations.",
                            'is_published': True,
                            'hourly_wage': 1100 + (i * 50), # Varying wage
                            'transportation_fee': 500,
                            'recruitment_count': 3
                        }
                    )
                    print(f"  Created Job: {store_data['name']} on {job_date}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == '__main__':
    populate_data()
