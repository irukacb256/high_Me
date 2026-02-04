from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import WorkerProfile, WorkerMembership, ExpHistory, Review
from business.models import JobApplication, WorkerReview

class AchievementService:
    @staticmethod
    def add_exp(worker_profile, amount, reason):
        """EXPを追加し、レベルアップ判定を行う"""
        membership, created = WorkerMembership.objects.get_or_create(worker=worker_profile)
        
        # 履歴作成
        ExpHistory.objects.create(
            worker=worker_profile,
            amount=amount,
            reason=reason
        )
        
        membership.current_exp += amount
        membership.save()
        
        # レベル計算
        AchievementService.update_level(membership)
        
        # グレード更新判定
        AchievementService.update_grade(worker_profile)

    @staticmethod
    def calculate_exp_from_minutes(minutes):
        """労働時間(分)から獲得EXPを計算 (1時間=500EXP)"""
        # Linear calculation: (minutes / 60) * 500
        # Rounding up or down? Usually int.
        return int((minutes / 60) * 500)

    @staticmethod
    def update_level(membership):
        """現在のEXPに基づいてレベルを更新する"""
        exp = membership.current_exp
        current_level = membership.level
        new_level = 1 # Default
        
        # Thresholds (Total EXP to REACH level):
        # Lv 2: 1000
        # Lv 3: 1000 + 2000 = 3000
        # Lv 4: 3000 + 3000 = 6000
        # Lv N (>=4): 6000 + (N-4)*3000
        
        if exp < 1000:
            new_level = 1
        elif exp < 3000:
            new_level = 2
        elif exp < 6000:
            new_level = 3
        else:
            # Lv 4 starts at 6000.
            # (exp - 6000) // 3000 gives how many additional levels above 4
            additional = (exp - 6000) // 3000
            new_level = 4 + additional
            
        if new_level > current_level:
            membership.level = new_level
            membership.save()
            return True # Leveled up
        return False

    @staticmethod
    def get_next_level_exp(membership):
        """次のレベルまでに必要なEXP残量を取得"""
        exp = membership.current_exp
        lvl = membership.level
        
        if lvl < 1:
            next_threshold = 1000
        elif lvl == 1:
            next_threshold = 1000
        elif lvl == 2:
            next_threshold = 3000
        elif lvl == 3:
            next_threshold = 6000
        else:
             next_threshold = 6000 + ((lvl + 1) - 4) * 3000
             
        return max(0, next_threshold - exp)

    @staticmethod
    def get_level_progress(membership):
        """現在のレベルにおける進捗率(0-100)を計算"""
        exp = membership.current_exp
        lvl = membership.level
        
        if lvl <= 1:
            prev_threshold = 0
            next_threshold = 1000
        elif lvl == 2:
            prev_threshold = 1000
            next_threshold = 3000
        elif lvl == 3:
            prev_threshold = 3000
            next_threshold = 6000
        else:
            # Lv N (>=4) starts at 6000 + (N-4)*3000
            prev_threshold = 6000 + (lvl - 4) * 3000
            next_threshold = prev_threshold + 3000
            
        level_range = next_threshold - prev_threshold
        current_in_level = exp - prev_threshold
        
        # Safety
        if current_in_level < 0: current_in_level = 0
        
        progress = int((current_in_level / level_range) * 100) if level_range > 0 else 0
        return min(100, max(0, progress))

    @staticmethod
    def calculate_stats(worker_profile):
        """実績画面用の統計情報を計算して返す"""
        # 1. 働いた回数 (JobApplication status='完了' かつ 過去)
        # Strictly speaking, completed jobs.
        # Check JobApplication with is_reward_paid=True or logic dependent
        # For now, distinct job postings worked.
        apps = JobApplication.objects.filter(worker=worker_profile.user, status='完了')
        work_count = apps.count()
        
        # 2. 働いた時間 (Total Hours)
        total_minutes = 0
        for app in apps:
            if app.attendance_at and app.leaving_at:
                diff = (app.leaving_at - app.attendance_at).total_seconds() / 60
                break_time = app.actual_break_duration if app.actual_break_duration > 0 else app.job_posting.break_duration
                work_min = max(0, diff - break_time)
                total_minutes += work_min
        
        total_hours = int(total_minutes // 60)
        
        # 3. Good率
        # WorkerReview (Store -> Worker)
        reviews = WorkerReview.objects.filter(worker=worker_profile.user)
        total_reviews = reviews.count()
        good_reviews = reviews.filter(review_type='good').count()
        
        if total_reviews > 0:
            good_rate = int((good_reviews / total_reviews) * 100)
        else:
            good_rate = 0 # Default? Or 100? Usually 0 if no work.
            
        return {
            'work_count': work_count,
            'total_hours': total_hours,
            'good_rate': good_rate,
            'good_count': good_reviews
        }

    @staticmethod
    def update_grade(worker_profile):
        """グレード昇格判定を行い更新する"""
        stats = AchievementService.calculate_stats(worker_profile)
        membership, _ = WorkerMembership.objects.get_or_create(worker=worker_profile)
        current_grade = membership.grade
        level = membership.level
        
        # 基準
        # ROOKIE -> HOPE: 1+ works, 1+ GOOD
        # HOPE -> ACE: 5+ works, Good>=90%, Lv > 5 (>=6)
        # ACE -> MASTER: 10+ works, Hours > 50, Good>=95%, Lv > 7 (>=8)
        
        # Check Master criteria first (top down or bottom up?)
        # User says "promote from X to Y". Usually implying you must be X to go to Y?
        # Or just "If you meet these stats, you are Master".
        # Let's assume absolute criteria.
        
        new_grade = 'ROOKIE'
        
        # Check Hope
        is_hope = stats['work_count'] >= 1 and stats['good_count'] >= 1
        
        # Check Ace
        is_ace = False
        if stats['work_count'] >= 5 and stats['good_rate'] >= 90 and level > 5:
            is_ace = True
            
        # Check Master
        is_master = False
        if stats['work_count'] >= 10 and stats['total_hours'] > 50 and stats['good_rate'] >= 95 and level > 7:
            is_master = True
            
        if is_master:
            new_grade = 'MASTER'
        elif is_ace:
            new_grade = 'ACE'
        elif is_hope:
            new_grade = 'HOPE'
        else:
            new_grade = 'ROOKIE'
            
        if new_grade != current_grade:
            # We could add logic to only allow promotion (not demotion) if desired, 
            # but usually stats based systems allow fluctuation. 
            # "Grade up criteria" implies promotion. 
            # If Good rate drops, do you drop to Ace? Usually yes in these apps.
            membership.grade = new_grade
            membership.save()
