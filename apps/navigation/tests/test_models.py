from django.test import TestCase
from datetime import time
from apps.navigation.models import ShuttleRoute, ShuttleSchedule


class ShuttleScheduleTestCase(TestCase):
    def setUp(self):
        self.route = ShuttleRoute.objects.create(
            name='기흥역 → 용인캠퍼스',
            origin='giheungstation',
            destination='yongin_campus',
            is_active=True
        )

    def test_get_next_departure_returns_soonest_time(self):
        """현재 시각 이후 가장 가까운 시간을 반환"""
        ShuttleSchedule.objects.create(
            route=self.route,
            departure_time=time(14, 30),
            day_type='weekday',
            is_active=True
        )
        ShuttleSchedule.objects.create(
            route=self.route,
            departure_time=time(16, 0),
            day_type='weekday',
            is_active=True
        )

        current_time = time(14, 15)
        next_shuttle = ShuttleSchedule.get_next_departure(self.route, current_time, 'weekday')

        self.assertIsNotNone(next_shuttle)
        self.assertEqual(next_shuttle.departure_time, time(14, 30))

    def test_get_next_departure_returns_none_after_last_run(self):
        """마지막 운행 이후 None 반환"""
        ShuttleSchedule.objects.create(
            route=self.route,
            departure_time=time(14, 30),
            day_type='weekday',
            is_active=True
        )

        current_time = time(15, 0)
        next_shuttle = ShuttleSchedule.get_next_departure(self.route, current_time, 'weekday')

        self.assertIsNone(next_shuttle)

    def test_inactive_schedule_excluded(self):
        """is_active=False인 시간표는 제외"""
        ShuttleSchedule.objects.create(
            route=self.route,
            departure_time=time(14, 30),
            day_type='weekday',
            is_active=False
        )
        ShuttleSchedule.objects.create(
            route=self.route,
            departure_time=time(16, 0),
            day_type='weekday',
            is_active=True
        )

        current_time = time(14, 15)
        next_shuttle = ShuttleSchedule.get_next_departure(self.route, current_time, 'weekday')

        self.assertIsNotNone(next_shuttle)
        self.assertEqual(next_shuttle.departure_time, time(16, 0))
