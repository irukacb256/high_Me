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
