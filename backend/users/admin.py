from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nip', 'created_at']
    search_fields = ['name', 'nip']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'company', 'is_staff']
    list_filter = ['role', 'is_staff', 'company']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra info', {'fields': ('role', 'company', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra info', {'fields': ('email', 'role', 'company', 'phone')}),
    )
