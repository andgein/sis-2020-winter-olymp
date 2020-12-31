from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login', views.login, name="login"),
    path('profile', views.profile, name="profile"),
    path('rules', views.rules, name="rules"),
    path('contests/<int:contest_id>/', views.view_contest, name="contest"),
    path('contests/<int:contest_id>/monitor/', views.monitor, name="monitor"),
    path('contests/<int:contest_id>/problems/<int:problem_id>/input/', views.problem_input, name="problem_input"),
    path('contests/<int:contest_id>/problems/<int:problem_id>/', views.problem, name="problem"),
    path('contests/<int:contest_id>/sabotages/close/', views.close_submission, name="close_submission"),
    path('contests/<int:contest_id>/sabotages/', views.create_sabotage, name="create_sabotage"),
    path('contests/<int:contest_id>/sabotages/check/', views.check_sabotages, name="check_sabotages"),
    path('contests/<int:contest_id>/sabotages/<int:sabotage_id>/', views.sabotage, name="sabotage"),
    path("sw.js", views.service_worker, name="service_worker"),
]
