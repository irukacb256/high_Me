
from business.models import JobPosting, JobTemplate, Store, BusinessProfile
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

def create_job():
    print("Starting creation...")
    # 1. Get or Create User/Business/Store
    user, _ = User.objects.get_or_create(username='dummy_store_owner', defaults={'email': 'dummy@example.com'})
    profile, _ = BusinessProfile.objects.get_or_create(
        user=user, 
        defaults={
            'company_name': 'Dummy Company',
            'business_type': 'Restaurant',
            'post_code': '000-0000',
            'prefecture': 'Tokyo',
            'city': 'Shibuya',
            'address_line': '1-1-1'
        }
    )
    
    store, _ = Store.objects.get_or_create(
        business=profile,
        store_name='【テスト】Dummy Store',
        defaults={
            'post_code': '000-0000',
            'prefecture': 'Tokyo',
            'city': 'Shibuya',
            'address_line': '1-1-1'
        }
    )
    
    # 2. Get or Create Template
    template, _ = JobTemplate.objects.get_or_create(
        store=store,
        title='【テスト】0:01-0:16 短時間業務',
        defaults={
            'industry': 'Restaurant',
            'occupation': 'Hall',
            'work_content': 'Test work content',
            'precautions': 'None',
            'address': 'Tokyo Shibuya 1-1-1',
            'contact_number': '090-0000-0000'
        }
    )
    
    # 3. Create JobPosting
    
    # Future Job (Tomorrow)
    date_tomorrow = timezone.now().date() + datetime.timedelta(days=1)
    
    JobPosting.objects.create(
        template=template,
        work_date=date_tomorrow,
        start_time=datetime.time(0, 1),
        end_time=datetime.time(0, 16),
        title=f"{template.title} (Future)",
        work_content=template.work_content,
        hourly_wage=1200,
        transportation_fee=500,
        recruitment_count=5,
        visibility='public',
        is_published=True
    )
    
    # Past Job (Today)
    date_today = timezone.now().date()
    
    JobPosting.objects.create(
        template=template,
        work_date=date_today,
        start_time=datetime.time(0, 1),
        end_time=datetime.time(0, 16),
        title=f"{template.title} (Past/Today)",
        work_content=template.work_content,
        hourly_wage=1200,
        transportation_fee=500,
        recruitment_count=5,
        visibility='public',
        is_published=True
    )

    print("Created dummy jobs for 0:01-0:16 (Today & Tomorrow)")

create_job()
