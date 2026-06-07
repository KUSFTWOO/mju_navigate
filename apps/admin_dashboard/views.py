from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse_lazy

from apps.admin_dashboard.mixins import StaffRequiredMixin
from apps.navigation.models import ShuttleRoute, ShuttleSchedule
from apps.academic.models import AcademicEvent

from .forms import ShuttleScheduleForm, AcademicEventForm


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 총 활성 회원 수
        total_users = User.objects.filter(is_active=True).count()

        # 오늘 운행 셔틀 수
        today = timezone.now()
        weekday = today.weekday()
        if weekday < 5:  # 월-금
            day_type = 'weekday'
        elif weekday == 5:  # 토
            day_type = 'saturday'
        else:  # 일
            day_type = 'sunday'

        today_shuttles = ShuttleSchedule.objects.filter(
            day_type=day_type,
            is_active=True
        ).count()

        # 오늘 이후 예정 이벤트 3건
        upcoming_events = AcademicEvent.objects.filter(
            start_date__gte=today.date()
        ).order_by('start_date')[:3]

        # 최근 가입 회원 5명
        recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:5]

        context.update({
            'total_users': total_users,
            'today_shuttles': today_shuttles,
            'upcoming_events': upcoming_events,
            'recent_users': recent_users,
        })

        return context


class ShuttleManageView(StaffRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/shuttle_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        routes = ShuttleRoute.objects.all().prefetch_related('schedules')

        context['routes'] = routes

        return context


class ShuttleScheduleCreateView(StaffRequiredMixin, CreateView):
    model = ShuttleSchedule
    form_class = ShuttleScheduleForm
    template_name = 'admin_dashboard/shuttle_schedule_form.html'
    success_url = reverse_lazy('admin_dashboard:shuttle')


class ShuttleScheduleUpdateView(StaffRequiredMixin, UpdateView):
    model = ShuttleSchedule
    form_class = ShuttleScheduleForm
    template_name = 'admin_dashboard/shuttle_schedule_form.html'
    success_url = reverse_lazy('admin_dashboard:shuttle')


class ShuttleScheduleDeleteView(StaffRequiredMixin, DeleteView):
    model = ShuttleSchedule
    template_name = 'admin_dashboard/shuttle_schedule_confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard:shuttle')


class AcademicEventManageView(StaffRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/academic_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        events = AcademicEvent.objects.all().order_by('-start_date')

        context['events'] = events

        return context


class AcademicEventCreateView(StaffRequiredMixin, CreateView):
    model = AcademicEvent
    form_class = AcademicEventForm
    template_name = 'admin_dashboard/academic_event_form.html'
    success_url = reverse_lazy('admin_dashboard:academic')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class AcademicEventUpdateView(StaffRequiredMixin, UpdateView):
    model = AcademicEvent
    form_class = AcademicEventForm
    template_name = 'admin_dashboard/academic_event_form.html'
    success_url = reverse_lazy('admin_dashboard:academic')


class AcademicEventDeleteView(StaffRequiredMixin, DeleteView):
    model = AcademicEvent
    template_name = 'admin_dashboard/academic_event_confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard:academic')


class UserManageView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'admin_dashboard/user_manage.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(email__icontains=q) | Q(profile__nickname__icontains=q)
            )

        return queryset


class UserToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
        except User.DoesNotExist:
            pass

        return render(
            request,
            'admin_dashboard/partials/user_row.html',
            {'user': user}
        )
