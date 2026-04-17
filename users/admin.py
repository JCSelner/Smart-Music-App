from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Feedback

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = BaseUserAdmin.list_display + ('role',) # type: ignore[operator]

admin.site.register(User, UserAdmin)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'topic', 'user', 'submitted_at')
    list_filter = ('subject',)
    readonly_fields = ('user', 'subject', 'topic', 'description', 'submitted_at')
