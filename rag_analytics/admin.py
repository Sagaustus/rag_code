from django.contrib import admin

from .models import DailyUsageSnapshot


@admin.register(DailyUsageSnapshot)
class DailyUsageSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "total_queries", "error_count", "created_at")
    ordering = ("-date",)
    readonly_fields = ("date", "total_queries", "error_count", "created_at")
