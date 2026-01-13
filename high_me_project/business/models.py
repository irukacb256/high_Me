# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField("会社名", max_length=100)
    business_type = models.CharField("事業形態", max_length=50) # 法人・個人
    is_verified = models.BooleanField("本人確認済み", default=False)
    verification_document = models.FileField("確認書類", upload_to='docs/', null=True, blank=True)

class Store(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    store_name = models.CharField("店舗名", max_length=100)
    post_code = models.CharField("郵便番号", max_length=7)
    prefecture = models.CharField("都道府県", max_length=20)
    city = models.CharField("市区町村名", max_length=100)
    address_line = models.CharField("町域・番地", max_length=100)
    building = models.CharField("建物名など", max_length=100, blank=True)

    def __str__(self):
        return self.store_name