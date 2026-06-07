from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    CAMPUS_CHOICES = [
        ('seoul', '서울캠퍼스'),
        ('yongin', '용인캠퍼스'),
        ('both', '양 캠퍼스'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='사용자'
    )
    nickname = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='닉네임'
    )
    campus = models.CharField(
        max_length=10,
        choices=CAMPUS_CHOICES,
        default='seoul',
        verbose_name='소속 캠퍼스'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필 목록'

    def __str__(self):
        return f"{self.user.email} ({self.get_campus_display()})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
