from django.contrib import admin
from .models import AcademicEvent


@admin.register(AcademicEvent)
class AcademicEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'campus', 'event_type', 'start_date', 'end_date')
    list_filter = ('campus', 'event_type', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'start_date', 'end_date')
        }),
        ('상세 정보', {
            'fields': ('description', 'campus', 'event_type')
        }),
        ('시스템', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  # 신규 생성
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
