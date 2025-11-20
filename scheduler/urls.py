from django.urls import path
from . import views

urlpatterns = [
    path('', views.input_schedule, name='input_schedule'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]