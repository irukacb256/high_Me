from django.contrib import admin
from .models import (
    BusinessProfile, Store, StoreGroupDefinition, StoreWorkerGroup,
    WorkerReview, StoreReview, StoreWorkerMemo, JobTemplate,
    JobTemplatePhoto, JobPosting, JobApplication, ChatRoom, Message,
    AttendanceCorrection, StoreMute, QualificationMaster
)

@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'business_type', 'is_verified')
    search_fields = ('company_name',)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'business', 'prefecture', 'city')
    search_fields = ('store_name',)

@admin.register(StoreGroupDefinition)
class StoreGroupDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'is_shared', 'is_system')
    list_filter = ('is_shared', 'is_system')

@admin.register(StoreWorkerGroup)
class StoreWorkerGroupAdmin(admin.ModelAdmin):
    list_display = ('store', 'worker', 'group_type', 'group_definition')
    list_filter = ('group_type',)

@admin.register(WorkerReview)
class WorkerReviewAdmin(admin.ModelAdmin):
    list_display = ('store', 'worker', 'review_type', 'created_at')
    list_filter = ('review_type',)

@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = ('store', 'worker', 'is_time_matched', 'is_content_matched', 'created_at')

@admin.register(StoreWorkerMemo)
class StoreWorkerMemoAdmin(admin.ModelAdmin):
    list_display = ('store', 'worker', 'updated_at')

class JobTemplatePhotoInline(admin.TabularInline):
    model = JobTemplatePhoto
    extra = 1

@admin.register(JobTemplate)
class JobTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'store', 'industry', 'occupation')
    inlines = [JobTemplatePhotoInline]

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'work_date', 'start_time', 'end_time', 'is_published')
    list_filter = ('work_date', 'is_published')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('worker', 'job_posting', 'status', 'applied_at', 'attendance_at', 'leaving_at')
    list_filter = ('status',)

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('store', 'worker', 'updated_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'created_at', 'is_read')

@admin.register(AttendanceCorrection)
class AttendanceCorrectionAdmin(admin.ModelAdmin):
    list_display = ('application', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(StoreMute)
class StoreMuteAdmin(admin.ModelAdmin):
    list_display = ('worker', 'store', 'created_at')

@admin.register(QualificationMaster)
class QualificationMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
