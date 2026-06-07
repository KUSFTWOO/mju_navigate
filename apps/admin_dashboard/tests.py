from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.navigation.models import ShuttleRoute, ShuttleSchedule
from apps.academic.models import AcademicEvent
from datetime import time, date


class DashboardAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123',
            is_staff=False
        )

    def test_dashboard_requires_staff(self):
        """비관리자는 대시보드 접근 불가"""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('admin_dashboard:index'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_allows_staff(self):
        """관리자는 대시보드 접근 가능"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin_dashboard:index'))
        self.assertEqual(response.status_code, 200)

    def test_non_staff_gets_403(self):
        """is_staff=False 유저는 403 반환"""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('admin_dashboard:shuttle'))
        self.assertEqual(response.status_code, 403)


class DashboardHomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.staff_user)

    def test_dashboard_displays_statistics(self):
        """대시보드에 통계 표시"""
        # 회원 생성
        User.objects.create_user(username='user1', email='user1@example.com', password='test')
        User.objects.create_user(username='user2', email='user2@example.com', password='test')

        response = self.client.get(reverse('admin_dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_users', response.context)
        self.assertEqual(response.context['total_users'], 3)  # staff_user + 2


class ShuttleManageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)

        # 셔틀 노선 생성
        self.route = ShuttleRoute.objects.create(
            name='기흥역 통학버스',
            origin='giheungstation',
            destination='yongin_campus'
        )

    def test_shuttle_manage_page_loads(self):
        """셔틀 관리 페이지 로드"""
        response = self.client.get(reverse('admin_dashboard:shuttle'))
        self.assertEqual(response.status_code, 200)

    def test_shuttle_create_adds_schedule(self):
        """셔틀 시간 추가"""
        response = self.client.post(
            reverse('admin_dashboard:shuttle_create'),
            {
                'route': self.route.id,
                'departure_time': '09:00',
                'day_type': 'weekday',
                'is_active': True
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShuttleSchedule.objects.count(), 1)


class UserToggleActiveTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_login(self.staff_user)

    def test_user_toggle_changes_is_active(self):
        """회원 활성/비활성 토글"""
        self.assertTrue(self.regular_user.is_active)

        response = self.client.post(
            reverse('admin_dashboard:user_toggle', kwargs={'pk': self.regular_user.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)


class AcademicEventManageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)

    def test_academic_event_create_sets_created_by(self):
        """학사일정 생성 시 created_by 자동 설정"""
        response = self.client.post(
            reverse('admin_dashboard:academic_create'),
            {
                'title': '중간고사',
                'start_date': '2026-04-13',
                'end_date': '2026-04-24',
                'campus': 'both',
                'event_type': 'exam',
                'description': '1학기 중간고사'
            }
        )

        self.assertEqual(response.status_code, 302)
        event = AcademicEvent.objects.get(title='중간고사')
        self.assertEqual(event.created_by, self.staff_user)
