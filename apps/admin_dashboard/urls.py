from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='index'),

    # 셔틀 관리
    path('shuttle/', views.ShuttleManageView.as_view(), name='shuttle'),
    path('shuttle/create/', views.ShuttleScheduleCreateView.as_view(), name='shuttle_create'),
    path('shuttle/<int:pk>/edit/', views.ShuttleScheduleUpdateView.as_view(), name='shuttle_edit'),
    path('shuttle/<int:pk>/delete/', views.ShuttleScheduleDeleteView.as_view(), name='shuttle_delete'),

    # 학사일정 관리
    path('academic/', views.AcademicEventManageView.as_view(), name='academic'),
    path('academic/create/', views.AcademicEventCreateView.as_view(), name='academic_create'),
    path('academic/<int:pk>/edit/', views.AcademicEventUpdateView.as_view(), name='academic_edit'),
    path('academic/<int:pk>/delete/', views.AcademicEventDeleteView.as_view(), name='academic_delete'),

    # 회원 관리
    path('users/', views.UserManageView.as_view(), name='users'),
    path('users/<int:pk>/toggle/', views.UserToggleActiveView.as_view(), name='user_toggle'),
]
