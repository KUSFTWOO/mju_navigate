from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('nickname', 'campus')
    verbose_name_plural = '프로필'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'nickname', 'campus', 'created_at')
    list_filter = ('campus', 'created_at')
    search_fields = ('user__email', 'nickname')
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = '이메일'
