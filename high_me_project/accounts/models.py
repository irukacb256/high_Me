from django.db import models
from django.contrib.auth.models import User

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # 生年月日を追加
    birth_date = models.DateField(null=True, blank=True)
    # シーケンス図にある詳細項目
    furigana = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    affiliation = models.CharField(max_length=100, blank=True) # 所属
    working_style = models.CharField(max_length=100, blank=True) # 働き方
    prefecture = models.CharField(max_length=50, blank=True) # 都道府県
    
    def __str__(self):
        return self.user.username