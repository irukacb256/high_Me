from django.db import models
from django.contrib.auth.models import User
from business.models import JobPosting, Store

class Job(models.Model):
    # (既存のコード - おそらく使われていないが残しておく)
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=100)
    reward = models.IntegerField()  # 金額
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    image_color = models.CharField(max_length=20, default="#50C878") # カードの色
    is_urgent = models.BooleanField(default=False) # 締切間近フラグ

    def __str__(self):
        return self.title

class FavoriteJob(models.Model):
    """求人のお気に入り"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_jobs')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job_posting')

class FavoriteStore(models.Model):
    """店舗のお気に入り"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_stores')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'store')