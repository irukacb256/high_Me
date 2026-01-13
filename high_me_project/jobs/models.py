from django.db import models

class Job(models.Model):
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