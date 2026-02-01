
from business.models import JobPosting, JobTemplate, Store, BusinessProfile
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

def create_job():
    print("Creating 0:10 - 0:30 Job...")
    
    # 1. Get Store
    user, _ = User.objects.get_or_create(username='dummy_store_owner', defaults={'email': 'dummy@example.com'})
    profile, _ = BusinessProfile.objects.get_or_create(user=user)
    store = Store.objects.filter(business=profile).first()
    if not store:
        # Fallback if creation part skipped
        store = Store.objects.first()
        
    print(f"Using Store: {store.store_name}")
    
    # 2. Get Template
    template, _ = JobTemplate.objects.get_or_create(
        store=store,
        title='【テスト】0:10-0:30 短時間業務',
        defaults={
            'industry': 'Restaurant',
            'occupation': 'Hall',
            'work_content': 'Test work content 0:10-0:30',
            'precautions': 'None',
            'address': 'Test Address',
            'contact_number': '090-0000-0000'
        }
    )
    
    # 3. Create JobPosting
    date_today = timezone.now().date()
    
    job = JobPosting.objects.create(
        template=template,
        work_date=date_today,
        start_time=datetime.time(0, 10),
        end_time=datetime.time(0, 30),
        title=f"{template.title} (Today/Future)",
        work_content=template.work_content,
        hourly_wage=1200,
        transportation_fee=500,
        recruitment_count=5,
        visibility='public',
        is_published=True
    )

    print(f"Created Job ID: {job.id} Title: {job.title}")
    print(f"Date: {job.work_date} Time: {job.start_time} - {job.end_time}")

create_job()
