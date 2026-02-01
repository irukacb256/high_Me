
from business.models import JobPosting, JobApplication
from accounts.models import WorkerProfile
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

def create_app():
    print("Finding job...")
    # Find the Past/Today job we created
    # Title contains "Past/Today"
    jobs = JobPosting.objects.filter(title__contains="Past/Today")
    if not jobs.exists():
        print("Job not found! Make sure verify_jobs script passed?")
        # Fallback: find ANY past job
        jobs = JobPosting.objects.filter(work_date__lt=timezone.now().date())
    
    if not jobs.exists():
        print("No past jobs found.")
        return

    job = jobs.last() # Pick one
    print(f"Using Job: {job.title} (ID: {job.id})")

    # Find a worker
    workers = WorkerProfile.objects.all()
    if not workers.exists():
        print("No workers found!")
        return
    
    worker_profile = workers.first()
    worker_user = worker_profile.user
    print(f"Using Worker: {worker_user.username} (ID: {worker_user.id})")

    # Create Application
    app, created = JobApplication.objects.get_or_create(
        job_posting=job,
        worker=worker_user,
        defaults={
            'status': '確定済み',
            'attendance_at': timezone.now(), # Dummy time
            'leaving_at': timezone.now(), # Dummy time
        }
    )
    
    if created:
        print(f"Created Application ID: {app.id}")
    else:
        print(f"Application already exists ID: {app.id}")

    # Ensure status is correct for review
    app.status = '確定済み'
    app.save()
    print("Status set to '確定済み'. You should be able to review now.")

create_app()
