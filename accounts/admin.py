from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'role', 'department', 'section']
    list_filter = ['role', 'department']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'