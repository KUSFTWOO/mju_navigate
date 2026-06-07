from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class StaffRequiredMixin(LoginRequiredMixin):
    """관리자(is_staff=True) 권한이 필요한 뷰."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())

        if not request.user.is_staff:
            return HttpResponseForbidden('관리자 권한이 필요합니다.')

        return super().dispatch(request, *args, **kwargs)
