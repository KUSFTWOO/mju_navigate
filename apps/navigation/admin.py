from django.contrib import admin
from .models import ShuttleRoute, ShuttleSchedule


class ShuttleScheduleInline(admin.TabularInline):
    model = ShuttleSchedule
    extra = 1
    fields = ('departure_time', 'day_type', 'is_active')


@admin.register(ShuttleRoute)
class ShuttleRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin', 'destination', 'is_active', 'created_at')
    list_filter = ('is_active', 'origin', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ShuttleScheduleInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShuttleSchedule)
class ShuttleScheduleAdmin(admin.ModelAdmin):
    list_display = ('route', 'departure_time', 'day_type', 'is_active')
    list_filter = ('day_type', 'is_active', 'route')
    search_fields = ('route__name',)
    readonly_fields = ('created_at', 'updated_at')
