from django.contrib import admin
from .models import (
    Badge, WorkerProfile, WorkerBadge, WorkerBankAccount,
    WalletTransaction, Review, QualificationCategory,
    QualificationItem, WorkerQualification, WorkerMembership,
    ExpHistory, PenaltyHistory
)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_name_kanji', 'first_name_kanji', 'is_identity_verified')
    search_fields = ('user__username', 'last_name_kanji', 'first_name_kanji')

@admin.register(WorkerBadge)
class WorkerBadgeAdmin(admin.ModelAdmin):
    list_display = ('worker', 'badge', 'is_obtained', 'certified_count')
    list_filter = ('is_obtained', 'badge')

@admin.register(WorkerBankAccount)
class WorkerBankAccountAdmin(admin.ModelAdmin):
    list_display = ('worker', 'bank_name', 'account_number', 'account_holder_name')

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('worker', 'transaction_type', 'amount', 'created_at')
    list_filter = ('transaction_type',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('worker', 'store_name', 'is_good', 'created_at')
    list_filter = ('is_good',)

@admin.register(QualificationCategory)
class QualificationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order')

@admin.register(QualificationItem)
class QualificationItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

@admin.register(WorkerQualification)
class WorkerQualificationAdmin(admin.ModelAdmin):
    list_display = ('worker', 'qualification', 'created_at')

@admin.register(WorkerMembership)
class WorkerMembershipAdmin(admin.ModelAdmin):
    list_display = ('worker', 'grade', 'level', 'current_exp')
    list_filter = ('grade',)

@admin.register(ExpHistory)
class ExpHistoryAdmin(admin.ModelAdmin):
    list_display = ('worker', 'amount', 'reason', 'created_at')

@admin.register(PenaltyHistory)
class PenaltyHistoryAdmin(admin.ModelAdmin):
    list_display = ('worker', 'points', 'reason', 'occurred_at')
