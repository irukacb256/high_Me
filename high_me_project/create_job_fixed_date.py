
from business.models import JobPosting, JobTemplate, Store, BusinessProfile
from django.contrib.auth.models import User
import datetime

def create_job():
    print("Creating 0:10 - 0:30 Job (Fixed Date: 2026-02-02)...")
    
    # 1. Get Store
    store = Store.objects.first()
    
    # 2. Get Template
    template, _ = JobTemplate.objects.get_or_create(
        store=store,
        title='【テスト】0:10-0:30 (JST Fixed)',
        defaults={
            'industry': 'Restaurant',
            'occupation': 'Hall',
            'work_content': 'Test work content 0:10-0:30 JST',
            'precautions': 'None',
            'address': 'Test Address',
            'contact_number': '090-0000-0000'
        }
    )
    
    # 3. Create JobPosting for 2026-02-02
    target_date = datetime.date(2026, 2, 2)
    
    job = JobPosting.objects.create(
        template=template,
        work_date=target_date,
        start_time=datetime.time(0, 10),
        end_time=datetime.time(0, 30),
        title=f"{template.title}",
        work_content=template.work_content,
        hourly_wage=1500, # Higher wage to stand out
        transportation_fee=500,
        recruitment_count=5,
        visibility='public',
        is_published=True
    )

    print(f"Created Job ID: {job.id} Title: {job.title}")
    print(f"Date: {job.work_date} Time: {job.start_time} - {job.end_time}")

create_job()
