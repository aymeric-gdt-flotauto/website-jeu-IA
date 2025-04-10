from django.contrib import admin
from .models import User, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('pseudonym', 'email', 'created_at', 'login_attempts', 'is_locked')
    search_fields = ('pseudonym', 'email')
    list_filter = ('created_at',)
    inlines = [ProfileInline]
    
    def is_locked(self, obj):
        return obj.is_account_locked()
    is_locked.boolean = True
    is_locked.short_description = 'Compte bloqué'
