from django import template
from business.models import AttendanceCorrection

register = template.Library()

@register.filter
def get_pending_correction_count(store):
    """
    指定された店舗に関連する勤怠修正依頼の未承認件数を返す
    """
    if not store:
        return 0
        
    return AttendanceCorrection.objects.filter(
        application__job_posting__template__store=store,
        status='pending'
    ).count()

@register.filter
def get_unreviewed_worker_count(store):
    """
    未レビューのワーカー数を返す
    """
    if not store:
        return 0
    
    from django.utils import timezone
    from business.models import JobApplication
    
    now = timezone.now()
    return JobApplication.objects.filter(
        job_posting__template__store=store,
        job_posting__end_time__lt=now,
        worker_review__isnull=True
    ).count()
