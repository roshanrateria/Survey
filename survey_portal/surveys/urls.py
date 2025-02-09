from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('surveys/', views.survey_list, name='survey_list'),
    path('survey/<int:survey_id>/', views.survey_detail, name='survey_detail'),
    path('survey/<int:survey_id>/statistics/', views.survey_statistics, name='survey_statistics'),
    path('survey/<int:survey_id>/responses/', views.survey_responses, name='survey_responses'),
    path('survey/create/', views.survey_create, name='survey_create'),
    path('survey/<int:survey_id>/edit/', views.survey_edit, name='survey_edit'),
    path('survey/<int:survey_id>/delete/', views.survey_delete, name='survey_delete'),
]
