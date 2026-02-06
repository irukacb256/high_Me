from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from business.models import Store, JobTemplate, JobPosting
from jobs.models import FavoriteJob, FavoriteStore
from django.urls import reverse

class FavoriteJobsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testworker', password='password')
        self.client = Client()
        self.client.login(username='testworker', password='password')
        
        # 店舗作成
        self.store = Store.objects.create(store_name="Test Store", business_name="Test Biz", phone="1234567890", address="Test Address", owner=User.objects.create_user(username='testowner'))
        
        # テンプレート作成
        self.template = JobTemplate.objects.create(store=self.store, title="Test Job Template", occupation="Cafe")
        
        # 求人作成 (本日)
        self.job1 = JobPosting.objects.create(
            template=self.template,
            title="Explicit Fav Job",
            work_date=timezone.now().date(),
            start_time="10:00:00",
            end_time="18:00:00",
            is_published=True,
            visibility='public',
            recruitment_count=1,
            hourly_wage=1000
        )
        
        self.job2 = JobPosting.objects.create(
            template=self.template,
            title="Store Fav Job",
            work_date=timezone.now().date(),
            start_time="11:00:00",
            end_time="19:00:00",
            is_published=True,
            visibility='public',
            recruitment_count=1,
            hourly_wage=1100
        )

    def test_explicit_favorite_appears(self):
        """個別にお気に入りした求人が表示されること"""
        FavoriteJob.objects.create(user=self.user, job_posting=self.job1)
        response = self.client.get(reverse('favorites'))
        self.assertEqual(response.status_code, 200)
        fav_jobs = response.context['favorite_jobs']
        self.assertTrue(any(nj.job_posting == self.job1 for nj in fav_jobs))

    def test_store_favorite_jobs_appear(self):
        """お気に入り店舗の求人が表示されること"""
        FavoriteStore.objects.create(user=self.user, store=self.store)
        response = self.client.get(reverse('favorites'))
        self.assertEqual(response.status_code, 200)
        fav_jobs = response.context['favorite_jobs']
        self.assertTrue(any(nj.job_posting == self.job2 for nj in fav_jobs))
        # is_from_store_fav フラグが立っていることも確認
        store_fav_job = next(nj for nj in fav_jobs if nj.job_posting == self.job2)
        self.assertTrue(getattr(store_fav_job, 'is_from_store_fav', False))

    def test_no_duplicate_jobs(self):
        """個別お気に入りとお気に入り店舗の両方に該当する場合、重複しないこと"""
        FavoriteJob.objects.create(user=self.user, job_posting=self.job1)
        FavoriteStore.objects.create(user=self.user, store=self.store)
        # job1 は両方に該当するはず
        response = self.client.get(reverse('favorites'))
        fav_jobs = response.context['favorite_jobs']
        job_ids = [nj.job_posting.id for nj in fav_jobs]
        self.assertEqual(job_ids.count(self.job1.id), 1)

    def test_only_recruiting_filter(self):
        """募集中の仕事のみフィルタリングが機能すること"""
        FavoriteStore.objects.create(user=self.user, store=self.store)
        
        # job3 を満員にする
        from jobs.models import JobApplication
        job3 = JobPosting.objects.create(
            template=self.template,
            title="Full Job",
            work_date=timezone.now().date(),
            start_time="12:00:00",
            end_time="20:00:00",
            is_published=True,
            visibility='public',
            recruitment_count=1,
            hourly_wage=1200
        )
        JobApplication.objects.create(job_posting=job3, worker=User.objects.create_user(username='otherworker'), status='確定済み')
        
        # フィルタなし: job1, job2, job3 (合計3件)
        response1 = self.client.get(reverse('favorites'))
        self.assertEqual(len(response1.context['favorite_jobs']), 3)
        
        # フィルタあり: job1, job2 (合計2件)
        response2 = self.client.get(reverse('favorites') + '?only_recruiting=1')
        fav_jobs2 = response2.context['favorite_jobs']
        self.assertEqual(len(fav_jobs2), 2)
        self.assertFalse(any(nj.job_posting == job3 for nj in fav_jobs2))
