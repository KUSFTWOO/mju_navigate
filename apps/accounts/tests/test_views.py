from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class ProfileViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_requires_login(self):
        """비로그인 상태에서 /accounts/profile/ 접근 시 로그인 페이지로 리다이렉트"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('account_login', response.url)

    def test_profile_view_get_authenticated(self):
        """로그인 후 프로필 페이지에 접근 가능"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_view_displays_user_info(self):
        """프로필 페이지에 사용자 정보가 표시"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, self.user.email)

    def test_profile_update_nickname_and_campus(self):
        """프로필 페이지에서 닉네임과 캠퍼스 수정 가능"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse('accounts:profile'),
            {
                'nickname': 'newuser',
                'campus': 'yongin'
            }
        )

        self.assertEqual(response.status_code, 302)

        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.nickname, 'newuser')
        self.assertEqual(updated_profile.campus, 'yongin')

    def test_profile_redirect_after_update(self):
        """프로필 수정 후 동일 페이지로 리다이렉트"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse('accounts:profile'),
            {
                'nickname': 'newuser',
                'campus': 'seoul'
            }
        )

        self.assertRedirects(response, reverse('accounts:profile'))
