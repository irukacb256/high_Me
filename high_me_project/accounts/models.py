from django.db import models
from django.contrib.auth.models import User

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # 画像1の項目
    birth_date = models.DateField(null=True, blank=True)
    real_name = models.CharField(max_length=100, blank=True)
    furigana = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    prefecture = models.CharField(max_length=50, blank=True)
    
    # 利用端末の設定（通知・位置情報）
    notifications_enabled = models.BooleanField(default=False)
    location_enabled = models.BooleanField(default=False)
    
    # 本人確認ステータス
    is_identity_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username