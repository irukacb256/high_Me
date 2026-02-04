
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import WorkerProfile
from business.models import JobApplication
from accounts.services import AchievementService

User = get_user_model()

def fix_exp():
    # Assuming the user is the one from the screenshot or the first worker
    # Inspect all workers
    for worker_profile in WorkerProfile.objects.all():
        user = worker_profile.user
        
        # Ensure membership exists
        if not hasattr(worker_profile, 'membership'):
             print(f"Skipping {user.username}: No membership found.")
             continue
             
        membership = worker_profile.membership
        print(f"Checking user: {user.username} (Current EXP: {membership.current_exp}, Level: {membership.level})")
        
        # Calculate expected EXP from completed jobs
        completed_apps = JobApplication.objects.filter(worker=user, status='完了')
        
        total_minutes = 0
        total_exp = 0
        
        print(f"  Found {completed_apps.count()} completed jobs.")
        
        for app in completed_apps:
            if app.attendance_at and app.leaving_at:
                duration_seconds = (app.leaving_at - app.attendance_at).total_seconds()
                dur_min = int(duration_seconds / 60)
                
                # Re-calculate work minutes using the same logic as views
                break_time = app.actual_break_duration if app.actual_break_duration > 0 else app.job_posting.break_duration
                # Clamp break time (retroactive fix logic)
                break_time = min(break_time, dur_min)
                
                work_min = max(0, dur_min - break_time)
                
                # Calculate EXP
                exp = AchievementService.calculate_exp_from_minutes(work_min)
                
                total_minutes += work_min
                total_exp += exp
                print(f"    Job {app.id}: {work_min} min -> {exp} EXP")
            else:
                print(f"    Job {app.id}: No time records")

        print(f"  Total Calculated Work Minutes: {total_minutes}")
        print(f"  Total Calculated EXP: {total_exp}")
        
        if total_exp > membership.current_exp:
            print(f"  !!! Mismatch Detected. Updating EXP from {membership.current_exp} to {total_exp} !!!")
            membership.current_exp = total_exp
            membership.save()
            
            # Update level
            start_level = membership.level
            AchievementService.update_level(membership)
            if membership.level > start_level:
                print(f"  !!! Leveled Up: {start_level} -> {membership.level} !!!")
        else:
            print("  EXP seems correct (or manual adjustments were made).")

if __name__ == '__main__':
    fix_exp()
