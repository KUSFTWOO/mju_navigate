from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.academic.models import AcademicEvent
from datetime import date


class AcademicEventModelTest(TestCase):
    def setUp(self):
        self.event = AcademicEvent.objects.create(
            title='중간고사',
            start_date=date(2026, 4, 13),
            end_date=date(2026, 4, 24),
            description='1학기 중간고사',
            campus='both',
            event_type='exam'
        )

    def test_event_str_returns_campus_and_title(self):
        self.assertEqual(str(self.event), '[공통] 중간고사 (2026-04-13)')

    def test_events_ordered_by_start_date(self):
        event2 = AcademicEvent.objects.create(
            title='기말고사',
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 12),
            campus='both',
            event_type='exam'
        )

        events = AcademicEvent.objects.all()
        self.assertEqual(list(events), [self.event, event2])

    def test_event_campus_display(self):
        self.assertEqual(self.event.get_campus_display(), '공통')

    def test_event_type_display(self):
        self.assertEqual(self.event.get_event_type_display(), '시험')


class AcademicCalendarViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event = AcademicEvent.objects.create(
            title='중간고사',
            start_date=date(2026, 4, 13),
            end_date=date(2026, 4, 24),
            campus='both',
            event_type='exam'
        )

    def test_calendar_view_returns_200(self):
        response = self.client.get(reverse('academic:index'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_contains_events(self):
        response = self.client.get(reverse('academic:index') + '?year=2026&month=4')
        self.assertContains(response, self.event.title)

    def test_calendar_view_template_used(self):
        response = self.client.get(reverse('academic:index'))
        self.assertTemplateUsed(response, 'academic/index.html')


class EventListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event_seoul = AcademicEvent.objects.create(
            title='서울캠 행사',
            start_date=date(2026, 4, 13),
            end_date=date(2026, 4, 13),
            campus='seoul',
            event_type='ceremony'
        )
        self.event_yongin = AcademicEvent.objects.create(
            title='용인캠 행사',
            start_date=date(2026, 4, 15),
            end_date=date(2026, 4, 15),
            campus='yongin',
            event_type='ceremony'
        )

    def test_event_list_filtered_by_campus(self):
        response = self.client.get(
            reverse('academic:event_list') + '?campus=seoul&year=2026&month=4'
        )
        self.assertContains(response, self.event_seoul.title)
        self.assertNotContains(response, self.event_yongin.title)

    def test_event_list_shows_both_when_all(self):
        response = self.client.get(
            reverse('academic:event_list') + '?campus=all&year=2026&month=4'
        )
        self.assertContains(response, self.event_seoul.title)
        self.assertContains(response, self.event_yongin.title)


class EventDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event = AcademicEvent.objects.create(
            title='기말고사',
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 12),
            description='1학기 기말고사입니다.',
            campus='both',
            event_type='exam'
        )

    def test_event_detail_returns_200(self):
        response = self.client.get(
            reverse('academic:event_detail', kwargs={'pk': self.event.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_event_detail_contains_title(self):
        response = self.client.get(
            reverse('academic:event_detail', kwargs={'pk': self.event.pk})
        )
        self.assertContains(response, self.event.title)

    def test_event_detail_template_used(self):
        response = self.client.get(
            reverse('academic:event_detail', kwargs={'pk': self.event.pk})
        )
        self.assertTemplateUsed(response, 'academic/partials/event_detail.html')
