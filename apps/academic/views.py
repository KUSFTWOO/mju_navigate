from django.shortcuts import render
from django.views.generic import TemplateView, View, DetailView
from django.utils import timezone
from datetime import timedelta, date
import calendar as cal_module
from .models import AcademicEvent


# ──────────────────────────────────────────────
# 달력 매트릭스 헬퍼
# ──────────────────────────────────────────────
def get_calendar_matrix(year, month, events):
    """
    월 달력 매트릭스 반환 (일요일 시작, 6주 × 7일).
    각 셀: {'day': int|None, 'types': [...], 'is_today': bool, 'is_sunday': bool, 'is_saturday': bool}
    """
    today = date.today()

    # 날짜 → 이벤트 유형 목록 매핑
    types_by_day: dict[int, list[str]] = {}
    for event in events:
        cur = event.start_date
        while cur <= event.end_date:
            if cur.year == year and cur.month == month:
                bucket = types_by_day.setdefault(cur.day, [])
                if event.event_type not in bucket:
                    bucket.append(event.event_type)
            cur += timedelta(days=1)

    c = cal_module.Calendar(firstweekday=6)   # 일요일 시작
    matrix = []
    for week in c.monthdayscalendar(year, month):
        row = []
        for col, day in enumerate(week):
            if day == 0:
                row.append({'day': None})
            else:
                row.append({
                    'day': day,
                    'types': types_by_day.get(day, []),
                    'is_today': (year == today.year and month == today.month and day == today.day),
                    'is_sunday': col == 0,
                    'is_saturday': col == 6,
                })
        matrix.append(row)
    return matrix


def get_month_bounds(year, month):
    """해당 월의 시작/종료 date 반환"""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def get_adjacent_months(year, month):
    """이전/다음 월 (year, month) 반환"""
    if month == 1:
        prev = (year - 1, 12)
    else:
        prev = (year, month - 1)
    if month == 12:
        nxt = (year + 1, 1)
    else:
        nxt = (year, month + 1)
    return prev, nxt


# ──────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────
class AcademicCalendarView(TemplateView):
    template_name = 'academic/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))
        campus = self.request.GET.get('campus', 'all')

        month_start, month_end = get_month_bounds(year, month)
        events = AcademicEvent.objects.filter(
            start_date__lte=month_end,
            end_date__gte=month_start,
        )
        if campus != 'all':
            events = events.filter(campus__in=[campus, 'both'])
        events = events.order_by('start_date')

        (prev_year, prev_month), (next_year, next_month) = get_adjacent_months(year, month)

        context.update({
            'events': events,
            'year': year,
            'month': month,
            'campus': campus,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'calendar_matrix': get_calendar_matrix(year, month, events),
        })
        return context


class EventListView(View):
    """HTMX 파셜 뷰 — 달력 그리드 + 이벤트 목록 반환"""

    def get(self, request):
        today = timezone.now().date()
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        campus = request.GET.get('campus', 'all')

        month_start, month_end = get_month_bounds(year, month)
        events = AcademicEvent.objects.filter(
            start_date__lte=month_end,
            end_date__gte=month_start,
        )
        if campus != 'all':
            events = events.filter(campus__in=[campus, 'both'])
        events = events.order_by('start_date')

        (prev_year, prev_month), (next_year, next_month) = get_adjacent_months(year, month)

        return render(request, 'academic/partials/event_list.html', {
            'events': events,
            'campus': campus,
            'year': year,
            'month': month,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'calendar_matrix': get_calendar_matrix(year, month, events),
        })


class EventDetailView(DetailView):
    model = AcademicEvent
    template_name = 'academic/partials/event_detail.html'
    context_object_name = 'event'
