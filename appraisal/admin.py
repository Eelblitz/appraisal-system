from django.contrib import admin
from .models import Appraisal, PartOne, PartTwo, PartThree, PartFour


@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'status', 'created_at']
    list_filter = ['status', 'cycle']
    search_fields = ['employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PartOne)
class PartOneAdmin(admin.ModelAdmin):
    list_display = ['appraisal', 'present_job', 'is_draft', 'submitted_at']
    list_filter = ['is_draft']


@admin.register(PartTwo)
class PartTwoAdmin(admin.ModelAdmin):
    list_display = ['appraisal', 'overall_rating', 'is_draft', 'submitted_at']
    list_filter = ['overall_rating', 'is_draft']


@admin.register(PartThree)
class PartThreeAdmin(admin.ModelAdmin):
    list_display = ['appraisal', 'promotion_fitness', 'long_term_potential', 'is_draft']


@admin.register(PartFour)
class PartFourAdmin(admin.ModelAdmin):
    list_display = ['appraisal', 'countersigning_officer', 'is_draft', 'submitted_at']