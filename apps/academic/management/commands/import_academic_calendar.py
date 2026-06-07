from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from apps.academic.models import AcademicEvent
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import re
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '명지대학교 학사일정을 웹에서 크롤링하여 DB에 저장합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help='학년도 (기본값: 현재년도)'
        )
        parser.add_argument(
            '--month',
            type=int,
            default=None,
            help='월 (1-12, 기본값: 전체)'
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='기존 데이터를 덮어쓸 것인지 여부'
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        replace = options['replace']

        self.stdout.write(f'명지대 학사일정 크롤링 시작 (연도: {year}, 월: {month or "전체"})')

        try:
            # 학사일정 크롤링
            events = self.crawl_calendar(year, month)
            if not events:
                self.stdout.write(self.style.WARNING('크롤링된 데이터가 없습니다'))
                return

            self.stdout.write(f'✓ 크롤링 완료: {len(events)}개 이벤트')

            # DB 저장 (upsert)
            saved_count = self.save_events(events, year, month, replace)
            self.stdout.write(
                self.style.SUCCESS(f'✓ 저장 완료: {saved_count}개 이벤트')
            )

        except Exception as e:
            raise CommandError(f'오류 발생: {str(e)}')

    def crawl_calendar(self, year, month=None):
        """
        명지대학교 학사일정 페이지에서 데이터 크롤링
        형식 예: **.05.25~.06.05** [학부·대학원] 강의평가 기간

        페이지: https://www.mju.ac.kr/mjukr/262/subview.do
        """
        url = 'https://www.mju.ac.kr/mjukr/262/subview.do'
        events = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                logger.warning(f'HTTP {response.status_code}')
                return events

            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()

            # 텍스트 기반 파싱
            events = self.parse_calendar_text(text_content, year)

            if events:
                logger.info(f'✓ {url}에서 {len(events)}개 이벤트 크롤링 완료')

        except requests.RequestException as e:
            logger.error(f'크롤링 오류: {str(e)}')

        return events

    def parse_calendar_row(self, cells, year):
        """테이블 행 파싱"""
        try:
            date_text = cells[0].get_text(strip=True)
            content = cells[-1].get_text(strip=True)

            if not date_text or not content:
                return None

            # 날짜 파싱 (.04 .13 ~ .05 .08 형식)
            dates = self.parse_date_range(date_text, year)
            if not dates:
                return None

            start_date, end_date = dates

            # 캠퍼스 및 이벤트 타입 분류
            campus = self.detect_campus(content)
            event_type = self.classify_event_type(content)

            return {
                'title': content,
                'start_date': start_date,
                'end_date': end_date,
                'campus': campus,
                'event_type': event_type,
                'description': '',
            }
        except Exception as e:
            logger.warning(f'행 파싱 오류: {str(e)}')
            return None

    def parse_calendar_text(self, text, year):
        """
        텍스트 기반 파싱
        형식: **.MM .DD ~ .MM .DD** [캠퍼스] 제목
        예: **.05 .25 ~ .06 .05** [학부·대학원] 강의평가 기간
        """
        events = []

        logger.info(f'파싱 시작: {len(text)} 자')

        # 여러 패턴 시도 (별표 개수 및 공백 변동에 대응)
        patterns = [
            # 패턴 1: **.MM .DD ~ .MM .DD** (별표 2개, 원래 형식)
            r'\*\*\.(\d{1,2})\s+\.(\d{1,2})\s*~\s*\.(\d{1,2})\s+\.(\d{1,2})\*\*\s+(.+?)(?=\n|$)',
            # 패턴 2: *.MM .DD ~ .MM .DD* (별표 1개)
            r'\*\.(\d{1,2})\s+\.(\d{1,2})\s*~\s*\.(\d{1,2})\s+\.(\d{1,2})\*\s+(.+?)(?=\n|$)',
            # 패턴 3: .MM .DD ~ .MM .DD (별표 없음)
            r'^\.(\d{1,2})\s+\.(\d{1,2})\s*~\s*\.(\d{1,2})\s+\.(\d{1,2})\s+(.+?)(?=\n|$)',
            # 패턴 4: **. MM . DD ~ . MM . DD** (공백 변동)
            r'\*\*\.\s*(\d{1,2})\s+\.\s*(\d{1,2})\s*~\s*\.\s*(\d{1,2})\s+\.\s*(\d{1,2})\*\*\s+(.+?)(?=\n|$)',
            # 패턴 5: **.MM.DD~.MM.DD** (공백 없음)
            r'\*\*\.(\d{1,2})\.(\d{1,2})~\.(\d{1,2})\.(\d{1,2})\*\*\s+(.+?)(?=\n|$)',
        ]

        for pattern_idx, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            if matches:
                logger.info(f'✓ 패턴 {pattern_idx + 1} 매칭: {len(matches)}개')

                for match in matches:
                    try:
                        start_month, start_day, end_month, end_day = map(int, match.groups()[:4])
                        content = match.group(5).strip()

                        # 유효성 검사
                        if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
                            logger.debug(f'  ✗ 유효하지 않은 월: {start_month}, {end_month}')
                            continue
                        if not (1 <= start_day <= 31 and 1 <= end_day <= 31):
                            logger.debug(f'  ✗ 유효하지 않은 일: {start_day}, {end_day}')
                            continue

                        if len(content) < 2:
                            continue

                        try:
                            start_date = date(year, start_month, start_day)
                            end_date = date(year, end_month, end_day)
                        except ValueError as ve:
                            logger.debug(f'  ✗ 날짜 변환 오류: {ve}')
                            continue

                        # 캠퍼스 및 이벤트 타입 분류
                        campus = self.detect_campus(content)
                        event_type = self.classify_event_type(content)

                        # 제목에서 캠퍼스 정보 제거
                        title = re.sub(r'\[.*?\]\s*', '', content).strip()

                        # 중복 확인
                        if not any(e['title'] == title and
                                 e['start_date'] == start_date and
                                 e['end_date'] == end_date and
                                 e['campus'] == campus for e in events):
                            events.append({
                                'title': title,
                                'start_date': start_date,
                                'end_date': end_date,
                                'campus': campus,
                                'event_type': event_type,
                                'description': '',
                            })
                            logger.info(f'  ✓ {title} ({start_date}~{end_date})')

                    except (ValueError, IndexError) as e:
                        logger.debug(f'행 파싱 오류: {str(e)}')
                        continue

                # 성공하면 다른 패턴 시도 안 함
                if events:
                    break

        logger.info(f'파싱 완료: {len(events)}개 이벤트')
        return events

    def parse_date_range(self, date_text, year):
        """
        날짜 범위 파싱
        형식: "04.13 ~ 05.08" 또는 ".04 .13 ~ .05 .08"
        """
        try:
            # 공백 정규화
            date_text = re.sub(r'\s+', ' ', date_text.strip())

            # 점(.) 제거 및 파싱
            parts = re.findall(r'(\d{1,2})', date_text)
            if len(parts) >= 4:
                start_month, start_day, end_month, end_day = map(int, parts[:4])

                if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
                    return None

                start_date = date(year, start_month, start_day)
                end_date = date(year, end_month, end_day)
                return start_date, end_date
        except (ValueError, IndexError):
            pass

        return None

    def detect_campus(self, text):
        """
        텍스트에서 캠퍼스 분류 감지
        [학부] 또는 [학 부] → 서울캠퍼스
        [대학원] → 용인캠퍼스
        [학부·대학원] 또는 둘 다 → 공통

        주의: 대괄호 안에 공백이 있을 수 있음 [학 부]
        """
        # 대괄호 안의 공백 제거 후 검색
        text_normalized = re.sub(r'[\s]+', '', text)

        has_undergrad = '학부' in text_normalized
        has_grad = '대학원' in text_normalized

        if has_undergrad and has_grad:
            return 'both'
        elif has_grad:
            return 'yongin'  # 대학원은 용인캠퍼스
        elif has_undergrad:
            return 'seoul'  # 학부는 서울캠퍼스
        else:
            return 'both'  # 캠퍼스 표기 없으면 공통

    def classify_event_type(self, text):
        """텍스트에서 이벤트 타입 자동 분류"""
        text_lower = text.lower()

        if any(kw in text for kw in ['휴강', '휴무', '공휴일', '방학', '휴일']):
            return 'holiday'
        elif any(kw in text for kw in ['시험', '중간고사', '기말고사', '수시고사']):
            return 'exam'
        elif any(kw in text for kw in ['수강신청', '신청']):
            return 'registration'
        elif any(kw in text for kw in ['식', '행사', '축제', '개교', '입학식', '졸업식', '학위']):
            return 'ceremony'
        else:
            return 'etc'

    def save_events(self, events, year, month=None, replace=False):
        """이벤트를 DB에 저장 (upsert)"""
        saved_count = 0
        admin_user = User.objects.filter(is_superuser=True).first()

        for event_data in events:
            # 필터 조건
            filters = {
                'title': event_data['title'],
                'start_date': event_data['start_date'],
                'end_date': event_data['end_date'],
                'campus': event_data['campus'],
            }

            if month and event_data['start_date'].month != month:
                continue

            # 기존 데이터 확인
            existing = AcademicEvent.objects.filter(**filters).first()

            if existing:
                if replace:
                    existing.event_type = event_data['event_type']
                    existing.description = event_data['description']
                    existing.save()
                    saved_count += 1
            else:
                # 새로 생성
                AcademicEvent.objects.create(
                    **event_data,
                    created_by=admin_user
                )
                saved_count += 1

        return saved_count
