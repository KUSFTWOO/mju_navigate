from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('', views.AcademicCalendarView.as_view(), name='index'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
]
