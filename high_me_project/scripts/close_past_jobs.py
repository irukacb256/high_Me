import os
import django
import sys
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobPosting, Store

def run():
    print("Updating/Creating past jobs...")
    
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    
    # Check if there are any jobs
    jobs = JobPosting.objects.all()
    count = jobs.count()
    print(f"Total jobs: {count}")
    
    # Move some jobs to yesterday if they are not already in the past
    # (Just specific ones to ensure we see them on calendar)
    
    # Or creating new ones if few
    store = Store.objects.first()
    if not store:
        print("No store found. Cannot create jobs.")
        return

    # Create 3 past jobs
    templates = store.jobtemplate_set.all()
    if not templates:
        print("No templates found.")
        return
        
    template = templates.first()
    
    for i in range(3):
        JobPosting.objects.create(
            template=template,
            work_date=yesterday,
            start_time=(now - timedelta(hours=5)).time(),
            end_time=(now - timedelta(hours=1)).time(),
            title=f"【過去・終了】ホールスタッフ {i+1}",
            work_content="過去の仕事です",
            recruitment_count=1,
            hourly_wage=1200,
            transportation_fee=500
        )
    print("Created 3 past jobs for yesterday.")

    # Check existing past jobs
    past_jobs = JobPosting.objects.filter(work_date__lt=today).count()
    print(f"Total past jobs: {past_jobs}")

if __name__ == '__main__':
    run()
