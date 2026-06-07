from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class UserProfileModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_auto_created_on_user_registration(self):
        """User 생성 시 UserProfile이 자동으로 생성되는지 확인"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_campus_default_is_seoul(self):
        """기본 캠퍼스가 서울캠퍼스인지 확인"""
        self.assertEqual(self.user.profile.campus, 'seoul')

    def test_profile_can_update_nickname(self):
        """닉네임을 수정할 수 있는지 확인"""
        self.user.profile.nickname = 'testuser'
        self.user.profile.save()

        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.nickname, 'testuser')

    def test_profile_can_update_campus(self):
        """캠퍼스를 수정할 수 있는지 확인"""
        self.user.profile.campus = 'yongin'
        self.user.profile.save()

        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.campus, 'yongin')

    def test_profile_str_representation(self):
        """프로필의 문자열 표현이 올바른지 확인"""
        expected_str = f"{self.user.email} (서울캠퍼스)"
        self.assertEqual(str(self.user.profile), expected_str)
