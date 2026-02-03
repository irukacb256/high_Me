from django.contrib import admin
from .models import FavoriteJob, FavoriteStore

@admin.register(FavoriteJob)
class FavoriteJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_posting', 'created_at')

@admin.register(FavoriteStore)
class FavoriteStoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'created_at')
