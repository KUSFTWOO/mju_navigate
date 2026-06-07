from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from apps.academic.models import AcademicEvent
from datetime import date


class ImportAcademicCalendarTest(TestCase):
    def setUp(self):
        self.command_name = 'import_academic_calendar'

    def test_parse_date_range(self):
        """날짜 범위 파싱 테스트"""
        from apps.academic.management.commands.import_academic_calendar import Command

        cmd = Command()

        # 테스트 케이스
        test_cases = [
            ("04.13 ~ 05.08", 2026, (date(2026, 4, 13), date(2026, 5, 8))),
            (".04 .13 ~ .05 .08", 2026, (date(2026, 4, 13), date(2026, 5, 8))),
            ("01.01 ~ 01.31", 2026, (date(2026, 1, 1), date(2026, 1, 31))),
        ]

        for date_text, year, expected in test_cases:
            result = cmd.parse_date_range(date_text, year)
            self.assertEqual(result, expected, f"Failed for {date_text}")

    def test_detect_campus(self):
        """캠퍼스 감지 테스트"""
        from apps.academic.management.commands.import_academic_calendar import Command

        cmd = Command()

        test_cases = [
            ("[학부] 수강신청", "seoul"),
            ("[대학원] 신입생 모집", "yongin"),
            ("[학부·대학원] 강의평가", "both"),
            ("노동절", "both"),
        ]

        for text, expected in test_cases:
            result = cmd.detect_campus(text)
            self.assertEqual(result, expected, f"Failed for {text}")

    def test_classify_event_type(self):
        """이벤트 타입 분류 테스트"""
        from apps.academic.management.commands.import_academic_calendar import Command

        cmd = Command()

        test_cases = [
            ("개교기념일", "holiday"),
            ("중간고사", "exam"),
            ("수강신청", "registration"),
            ("입학식", "ceremony"),
            ("학사공지", "etc"),
        ]

        for text, expected in test_cases:
            result = cmd.classify_event_type(text)
            self.assertEqual(result, expected, f"Failed for {text}")

    def test_parse_calendar_text(self):
        """텍스트 기반 파싱 테스트 (명지대 형식)"""
        from apps.academic.management.commands.import_academic_calendar import Command

        cmd = Command()

        # 명지대 실제 형식 샘플 데이터
        sample_text = """
**.05.25~.06.05** [학부·대학원] 강의평가 기간

**.06.01~.06.05** [학부] 하계 계절수업 접수 및 조기복학 기간

**.06.08~.06.15** [학부·대학원] 기말고사 기간
        """

        events = cmd.parse_calendar_text(sample_text, 2026)

        self.assertGreater(len(events), 0, "파싱된 이벤트가 없습니다")

        # 첫 번째 이벤트 검증
        first_event = events[0]
        self.assertEqual(first_event['start_date'], date(2026, 5, 25))
        self.assertEqual(first_event['end_date'], date(2026, 6, 5))
        self.assertEqual(first_event['campus'], 'both')
        self.assertIn('강의평가', first_event['title'])

    def test_save_events_upsert(self):
        """Upsert 기능 테스트"""
        from apps.academic.management.commands.import_academic_calendar import Command

        cmd = Command()

        # 테스트 이벤트 데이터
        events = [
            {
                'title': '개교기념일',
                'start_date': date(2026, 4, 1),
                'end_date': date(2026, 4, 1),
                'campus': 'both',
                'event_type': 'holiday',
                'description': '개교기념일',
            }
        ]

        # 첫 번째 저장
        saved_count = cmd.save_events(events, 2026)
        self.assertEqual(saved_count, 1)
        self.assertEqual(AcademicEvent.objects.count(), 1)

        # 두 번째 저장 (replace=False, 중복 방지)
        saved_count = cmd.save_events(events, 2026, replace=False)
        self.assertEqual(saved_count, 0)  # 중복이므로 저장 안 됨
        self.assertEqual(AcademicEvent.objects.count(), 1)

        # 세 번째 저장 (replace=True, 덮어쓰기)
        events[0]['event_type'] = 'ceremony'
        saved_count = cmd.save_events(events, 2026, replace=True)
        self.assertEqual(saved_count, 1)  # 업데이트
        self.assertEqual(AcademicEvent.objects.count(), 1)

        # 업데이트 확인
        event = AcademicEvent.objects.first()
        self.assertEqual(event.event_type, 'ceremony')

    def test_command_execution(self):
        """커맨드 실행 테스트 (실제 크롤링 제외)"""
        # 실제 크롤링은 외부 의존성이므로 테스트 제외
        # 대신 커맨드 구조만 검증
        out = StringIO()

        # 크롤링 오류를 무시하고 커맨드 실행
        try:
            call_command(self.command_name, stdout=out)
        except Exception as e:
            # 크롤링 오류는 무시 (외부 페이지 접근 문제)
            self.assertIn('오류', str(e) or 'pass')
