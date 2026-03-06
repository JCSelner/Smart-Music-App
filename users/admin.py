from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = BaseUserAdmin.list_display + ('role',) # type: ignore[operator]

admin.site.register(User, UserAdmin)
