from django.db import models
from django.contrib.auth.models import User


class AcademicEvent(models.Model):
    CAMPUS_CHOICES = [
        ('seoul', '서울캠퍼스'),
        ('yongin', '용인캠퍼스'),
        ('both', '공통'),
    ]

    EVENT_TYPE_CHOICES = [
        ('holiday', '공휴일/휴강'),
        ('exam', '시험'),
        ('registration', '수강신청'),
        ('ceremony', '행사/식'),
        ('etc', '기타'),
    ]

    title = models.CharField(max_length=200, verbose_name='일정 제목')
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    description = models.TextField(blank=True, verbose_name='상세 설명')
    campus = models.CharField(
        max_length=10,
        choices=CAMPUS_CHOICES,
        default='both',
        verbose_name='해당 캠퍼스'
    )
    event_type = models.CharField(
        max_length=15,
        choices=EVENT_TYPE_CHOICES,
        default='etc',
        verbose_name='일정 유형'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='academic_events',
        verbose_name='등록자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '학사일정'
        verbose_name_plural = '학사일정 목록'
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['campus']),
        ]

    def __str__(self):
        return f"[{self.get_campus_display()}] {self.title} ({self.start_date})"
