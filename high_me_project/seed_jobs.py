import os
import django
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
settings.ALLOWED_HOSTS += ['testserver']

from business.models import JobPosting, JobTemplate, BusinessProfile, Store
from django.contrib.auth.models import User

def seed_jobs():
    print("--- Seeding Jobs ---")
    
    # Ensure Business and Store exist
    u, _ = User.objects.get_or_create(username='biz_owner')
    u.set_password('password')
    u.save()
    
    biz, _ = BusinessProfile.objects.get_or_create(user=u, defaults={
        'company_name': 'Test Company',
        'business_type': 'Retail'
    })
    
    store_tokyo, _ = Store.objects.get_or_create(business=biz, store_name='Tokyo Store', defaults={
        'post_code': '1000001',
        'prefecture': '東京都',
        'city': 'Chiyoda',
        'address_line': '1-1'
    })
    
    store_kanagawa, _ = Store.objects.get_or_create(business=biz, store_name='Kanagawa Store', defaults={
        'post_code': '2000001',
        'prefecture': '神奈川県',
        'city': 'Yokohama',
        'address_line': '1-1'
    })
    
    # Create Templates
    tmpl_tokyo, _ = JobTemplate.objects.get_or_create(store=store_tokyo, title='Tokyo Staff', defaults={
        'industry': 'Retail',
        'occupation': '販売',
        'work_content': 'Sales',
        'precautions': 'None',
        'address': 'Tokyo Address',
        'contact_number': '0300000000'
    })

    tmpl_kanagawa, _ = JobTemplate.objects.get_or_create(store=store_kanagawa, title='Kanagawa Staff', defaults={
        'industry': 'Retail',
        'occupation': '販売',
        'work_content': 'Sales',
        'precautions': 'None',
        'address': 'Kanagawa Address',
        'contact_number': '0450000000'
    })
    
    # Create JobPostings for Today and Tomorrow
    today = timezone.localdate()
    
    # Tokyo Job Today
    JobPosting.objects.get_or_create(
        template=tmpl_tokyo,
        work_date=today,
        start_time=datetime.strptime('10:00', '%H:%M').time(),
        end_time=datetime.strptime('18:00', '%H:%M').time(),
        defaults={
            'title': 'Tokyo Retail Staff Today',
            'is_published': True,
            'hourly_wage': 1200
        }
    )
    print(f"Created/Found Job: Tokyo Today ({today})")

    # Kanagawa Job Today
    JobPosting.objects.get_or_create(
        template=tmpl_kanagawa,
        work_date=today,
        start_time=datetime.strptime('09:00', '%H:%M').time(),
        end_time=datetime.strptime('17:00', '%H:%M').time(),
        defaults={
            'title': 'Kanagawa Retail Staff Today',
            'is_published': True,
            'hourly_wage': 1150
        }
    )
    print(f"Created/Found Job: Kanagawa Today ({today})")
    
    # Tokyo Job Tomorrow
    JobPosting.objects.get_or_create(
        template=tmpl_tokyo,
        work_date=today + timedelta(days=1),
        start_time=datetime.strptime('10:00', '%H:%M').time(),
        end_time=datetime.strptime('18:00', '%H:%M').time(),
        defaults={
            'title': 'Tokyo Retail Staff Tomorrow',
            'is_published': True,
            'hourly_wage': 1200
        }
    )
    print(f"Created/Found Job: Tokyo Tomorrow ({today + timedelta(days=1)})")

if __name__ == '__main__':
    seed_jobs()
