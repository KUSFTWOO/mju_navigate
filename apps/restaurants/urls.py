from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('', views.RestaurantView.as_view(), name='index'),
    path('search/', views.RestaurantSearchView.as_view(), name='search'),
]
