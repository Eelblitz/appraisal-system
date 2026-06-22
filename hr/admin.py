from django.contrib import admin
from .models import (
    AppraisalCategory, AppraisalCycle,
    PerformanceAspect, AppraisalTemplate, TemplateAspect
)


@admin.register(AppraisalCategory)
class AppraisalCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


class TemplateAspectInline(admin.TabularInline):
    # This lets HR add/remove aspects directly inside the Template admin page
    model = TemplateAspect
    extra = 1
    ordering = ['order']


@admin.register(AppraisalTemplate)
class AppraisalTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'cycle', 'is_active', 'created_at']
    inlines = [TemplateAspectInline]


@admin.register(AppraisalCycle)
class AppraisalCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'status', 'download_fee', 'period_from', 'period_to']
    list_filter = ['status', 'year']
    search_fields = ['name']


@admin.register(PerformanceAspect)
class PerformanceAspectAdmin(admin.ModelAdmin):
    list_display = ['label', 'order', 'is_applicable']
    list_editable = ['order']  # HR can reorder aspects directly in the list view
    ordering = ['order']