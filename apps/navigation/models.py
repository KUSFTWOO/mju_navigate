from django.db import models
from datetime import time


class ShuttleRoute(models.Model):
    ORIGIN_CHOICES = [
        ('mjustation', '명지대역'),
        ('giheungstation', '기흥역'),
        ('seoul_campus', '서울캠퍼스'),
        ('yongin_campus', '용인캠퍼스'),
    ]

    name = models.CharField(max_length=100, verbose_name='노선명')
    origin = models.CharField(max_length=30, choices=ORIGIN_CHOICES, verbose_name='출발지')
    destination = models.CharField(max_length=30, choices=ORIGIN_CHOICES, verbose_name='도착지')
    description = models.TextField(blank=True, verbose_name='노선 설명')
    is_active = models.BooleanField(default=True, verbose_name='운행 여부')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '셔틀 노선'
        verbose_name_plural = '셔틀 노선 목록'
        ordering = ['origin', 'destination']

    def __str__(self):
        return f"{self.get_origin_display()} → {self.get_destination_display()}"


class ShuttleSchedule(models.Model):
    DAY_TYPE_CHOICES = [
        ('weekday', '평일'),
        ('saturday', '토요일'),
        ('sunday', '일요일/공휴일'),
    ]

    route = models.ForeignKey(
        ShuttleRoute,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='운행 노선'
    )
    departure_time = models.TimeField(verbose_name='출발 시각')
    day_type = models.CharField(
        max_length=10,
        choices=DAY_TYPE_CHOICES,
        default='weekday',
        verbose_name='운행 요일 구분'
    )
    is_active = models.BooleanField(default=True, verbose_name='운행 여부')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '셔틀 시간표'
        verbose_name_plural = '셔틀 시간표 목록'
        ordering = ['departure_time']
        indexes = [
            models.Index(fields=['route', 'day_type', 'is_active']),
            models.Index(fields=['departure_time']),
        ]

    def __str__(self):
        return f"{self.route} {self.get_day_type_display()} {self.departure_time}"

    @classmethod
    def get_next_departure(cls, route, current_time, day_type='weekday'):
        """현재 시각 이후 가장 가까운 출발 시각을 반환한다."""
        return cls.objects.filter(
            route=route,
            day_type=day_type,
            is_active=True,
            departure_time__gte=current_time
        ).order_by('departure_time').first()
