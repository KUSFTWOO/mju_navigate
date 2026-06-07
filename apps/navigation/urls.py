from django.urls import path
from . import views

app_name = 'navigation'

urlpatterns = [
    path('', views.NavigationView.as_view(), name='index'),
    path('search/', views.RouteSearchView.as_view(), name='search'),
    path('select/', views.RouteSelectView.as_view(), name='select'),
    path('loadlane/', views.LoadLaneView.as_view(), name='loadlane'),
    path('shuttle/timetable/', views.ShuttleTimetableView.as_view(), name='shuttle_timetable'),
    path('shuttle/', views.ShuttleView.as_view(), name='shuttle'),
]
