from django.contrib import admin
from .models import (
    Analysis, AnalysisRun, BugLocalization, SuspiciousFileScore,
    RootCause, Patch, PatchValidation, Report,
)

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'status', 'user', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'project__name']

@admin.register(AnalysisRun)
class AnalysisRunAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'step', 'status', 'started_at', 'completed_at']
    list_filter = ['step', 'status']

@admin.register(BugLocalization)
class BugLocalizationAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'summary', 'created_at']

@admin.register(SuspiciousFileScore)
class SuspiciousFileScoreAdmin(admin.ModelAdmin):
    list_display = ['localization', 'file_path', 'suspicion_score', 'rank']

@admin.register(RootCause)
class RootCauseAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'root_file', 'confidence', 'created_at']

@admin.register(Patch)
class PatchAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'status', 'summary', 'created_at']

@admin.register(PatchValidation)
class PatchValidationAdmin(admin.ModelAdmin):
    list_display = ['patch', 'tests_passed', 'tests_failed', 'overall_score']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'format', 'created_at']
