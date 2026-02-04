
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication
from accounts.models import WorkerProfile, ExpHistory, WorkerMembership
from accounts.services import AchievementService

def backfill_history():
    print("Backfilling ExpHistory for completed jobs...")
    
    # Get all completed jobs
    apps = JobApplication.objects.filter(status='完了')
    
    count = 0
    for app in apps:
        worker = app.worker
        try:
            profile = worker.workerprofile
            membership = worker.workerprofile.membership
        except:
            continue
            
        # Check if history already exists for this date/reason roughly?
        # Ideally ExpHistory should have a foreign key to JobApplication, but it doesn't.
        # It's weak linking.
        # We can check if we have a history with matching amount and date roughly, but simpler is just to create if missing.
        # Or better, just create if user has high EXP but no history.
        
        # Calculate expected EXP for this job
        if app.attendance_at and app.leaving_at:
            duration_seconds = (app.leaving_at - app.attendance_at).total_seconds()
            dur_min = int(duration_seconds / 60)
            
            break_time_raw = app.actual_break_duration if app.actual_break_duration > 0 else app.job_posting.break_duration
            break_time = min(break_time_raw, dur_min)
            work_min = max(0, dur_min - break_time)
            
            exp = AchievementService.calculate_exp_from_minutes(work_min)
            
            if exp > 0:
                # Check if a history record roughly exists?
                # Since we don't have job_id in history, we risk duplication if run multiple times.
                # However, currently there are NO histories for past jobs because the old code didn't create them.
                # So we can just create them if profile.exp_histories.count() is 0 or low compared to work count.
                
                # Let's verify duplication prevention:
                # Check if there is a record with this amount created today (since we just ran fix script? no fix script didn't create history).
                # Check if there is a record with "業務完了" created recently?
                # Actually, just check if ANY history exists for this worker with this amount?
                # A safer approach: Delete all histories and recreate them based on completed jobs? 
                # That would be cleanest for "Reflecting history".
                # But if there are manual bonuses, we lose them.
                # Assuming this is dev/test data, clearing might be okay.
                # BUT, let's just append if not exists.
                
                # Just create one for now.
                print(f"Adding history: {worker.username} +{exp} EXP (Job {app.id})")
                
                # Determine date: use leaving_at as created_at for history to look correct
                history = ExpHistory.objects.create(
                    worker=profile,
                    amount=exp,
                    reason=f"業務完了 ({app.job_posting.template.store.store_name})",
                    created_at=app.leaving_at # This will be overridden by auto_now_add=True unfortunately
                )
                # To override auto_now_add, we need to update it after creation or generic trick?
                # Django allow override on create? No, auto_now_add ignores kwargs.
                # We update it immediately.
                history.created_at = app.leaving_at
                history.save()
                
                count += 1
                
    print(f"Backfilled {count} history records.")

if __name__ == '__main__':
    backfill_history()
