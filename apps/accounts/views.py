from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserProfile


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        return context

    def post(self, request, *args, **kwargs):
        profile = request.user.profile
        nickname = request.POST.get('nickname', '')
        campus = request.POST.get('campus', 'seoul')

        profile.nickname = nickname
        profile.campus = campus
        profile.save()

        return redirect('accounts:profile')
