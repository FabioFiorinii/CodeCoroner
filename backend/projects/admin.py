from django.contrib import admin
from .models import Project, ProjectMembership

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name', 'created_by__email']

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'created_at']
    search_fields = ['project__name', 'user__email']
