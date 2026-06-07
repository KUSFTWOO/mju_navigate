from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.academic.models import AcademicEvent
from datetime import date


class Command(BaseCommand):
    help = '학사일정 크롤러 테스트 (샘플 데이터 사용)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=2026,
            help='학년도'
        )

    def handle(self, *args, **options):
        year = options['year']

        self.stdout.write(f'\n학사일정 크롤러 테스트 (연도: {year})')
        self.stdout.write('=' * 60)

        # 샘플 데이터 (명지대 실제 형식)
        # 형식: **.MM.DD~.MM.DD** [캠퍼스] 제목
        sample_events = [
            {
                'title': '강의평가 기간',
                'start_date': date(year, 5, 25),
                'end_date': date(year, 6, 5),
                'campus': 'both',
                'event_type': 'etc',
                'description': '[학부·대학원] 강의평가 기간',
            },
            {
                'title': '하계 계절수업 접수 및 조기복학 기간',
                'start_date': date(year, 6, 1),
                'end_date': date(year, 6, 5),
                'campus': 'seoul',
                'event_type': 'registration',
                'description': '[학부] 하계 계절수업 접수 및 조기복학 기간',
            },
            {
                'title': '제9회 전국동시지방선거',
                'start_date': date(year, 6, 3),
                'end_date': date(year, 6, 3),
                'campus': 'both',
                'event_type': 'holiday',
                'description': '전국동시지방선거',
            },
            {
                'title': '기말고사 기간',
                'start_date': date(year, 6, 8),
                'end_date': date(year, 6, 15),
                'campus': 'both',
                'event_type': 'exam',
                'description': '[학부·대학원] 기말고사 기간',
            },
            {
                'title': '개교기념일',
                'start_date': date(year, 3, 23),
                'end_date': date(year, 3, 23),
                'campus': 'both',
                'event_type': 'ceremony',
                'description': '명지대학교 개교기념일',
            },
            {
                'title': '1학기 수강신청',
                'start_date': date(year, 11, 18),
                'end_date': date(year, 11, 22),
                'campus': 'seoul',
                'event_type': 'registration',
                'description': '[학부] 1학기 수강신청',
            },
            {
                'title': '2학기 수강신청',
                'start_date': date(year, 8, 5),
                'end_date': date(year, 8, 9),
                'campus': 'yongin',
                'event_type': 'registration',
                'description': '[대학원] 2학기 수강신청',
            },
            {
                'title': '중간고사 기간',
                'start_date': date(year, 4, 20),
                'end_date': date(year, 4, 27),
                'campus': 'both',
                'event_type': 'exam',
                'description': '[학부·대학원] 중간고사 기간',
            },
        ]

        self.stdout.write(f'\n샘플 데이터: {len(sample_events)}개\n')

        # 데이터 저장
        admin_user = User.objects.filter(is_superuser=True).first()
        created_count = 0
        existing_count = 0

        for event_data in sample_events:
            # 중복 확인
            filters = {
                'title': event_data['title'],
                'start_date': event_data['start_date'],
                'end_date': event_data['end_date'],
                'campus': event_data['campus'],
            }

            existing = AcademicEvent.objects.filter(**filters).first()

            if existing:
                existing_count += 1
                self.stdout.write(
                    f"⊘ 이미 존재: {event_data['title']} ({event_data['start_date']})"
                )
            else:
                AcademicEvent.objects.create(
                    **event_data,
                    created_by=admin_user
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ 추가: {event_data['title']} ({event_data['start_date']})"
                    )
                )

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ 완료: 추가 {created_count}개, 기존 {existing_count}개'
            )
        )

        # 저장된 이벤트 요약
        self.stdout.write('\n저장된 학사일정 요약:')
        self.stdout.write('-' * 60)

        events_by_type = {}
        events_by_campus = {}

        for event in AcademicEvent.objects.all():
            # 타입별
            event_type = event.get_event_type_display()
            if event_type not in events_by_type:
                events_by_type[event_type] = 0
            events_by_type[event_type] += 1

            # 캠퍼스별
            campus = event.get_campus_display()
            if campus not in events_by_campus:
                events_by_campus[campus] = 0
            events_by_campus[campus] += 1

        self.stdout.write('\n[이벤트 타입별]')
        for event_type, count in sorted(events_by_type.items()):
            self.stdout.write(f"  {event_type}: {count}개")

        self.stdout.write('\n[캠퍼스별]')
        for campus, count in sorted(events_by_campus.items()):
            self.stdout.write(f"  {campus}: {count}개")

        total = AcademicEvent.objects.count()
        self.stdout.write(f'\n총 {total}개 학사일정 저장됨')
