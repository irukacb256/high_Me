
import os
import django
from datetime import date, timedelta, time
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobTemplate, JobPosting
from django.utils import timezone

def run():
    print("Starting job seeding...")
    
    # Get all active templates
    templates = JobTemplate.objects.all()
    
    if not templates.exists():
        print("No templates found! Please create some templates first.")
        return

    # Target period: Tomorrow to Feb 10, 2026
    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 10)
    
    # Ensure start date is not after end date (sanity check)
    if start_date > end_date:
        # If we are already past Feb 2, just start from tomorrow
        start_date = timezone.now().date() + timedelta(days=1)
        if start_date > end_date:
             print("Current date is already past Feb 10, 2026. Adjusting target range.")
             # If completely past, maybe the user means next year or just "until feb 10" implies future relative to now?
             # Given 2026-02-01 context, 2026-02-02 to 2026-02-10 is valid.
             pass

    print(f"Generating jobs from {start_date} to {end_date}...")
    
    created_count = 0
    
    current_date = start_date
    while current_date <= end_date:
        print(f"Processing date: {current_date}")
        
        for template in templates:
            # Check if a posting already exists for this template on this date
            if JobPosting.objects.filter(template=template, work_date=current_date).exists():
                continue
                
            # Randomize time slightly based on typical shifts? Or just fixed.
            # User said: "Current stores and postings... same content or changed time"
            # Let's try to mimic existing postings for this template if any, otherwise default.
            
            existing_postings = JobPosting.objects.filter(template=template).order_by('-created_at')
            if existing_postings.exists():
                ref_post = existing_postings.first()
                start_time = ref_post.start_time
                end_time = ref_post.end_time
                hourly_wage = ref_post.hourly_wage
                transportation_fee = ref_post.transportation_fee
                work_content = ref_post.work_content
            else:
                # Default values if no prior posting exists
                start_time = time(10, 0)
                end_time = time(15, 0)
                hourly_wage = 1100
                transportation_fee = 500
                work_content = template.work_content
            
            # Create the posting
            JobPosting.objects.create(
                template=template,
                work_date=current_date,
                start_time=start_time,
                end_time=end_time,
                title=template.title,
                work_content=work_content,
                hourly_wage=hourly_wage,
                transportation_fee=transportation_fee,
                recruitment_count=1, # Default
                break_duration=60 if (end_time.hour - start_time.hour) >= 6 else 0,
                is_published=True
            )
            created_count += 1
            
        current_date += timedelta(days=1)
        
    print(f"Completed! Created {created_count} new job postings.")

if __name__ == '__main__':
    run()
