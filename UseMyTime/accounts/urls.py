from django.urls import path, include
from . import views

urlpatterns = [
    # Пути и представления для входа, смены и сброса пароля
    path('', include('django.contrib.auth.urls')),

    path('', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='profile_edit'),
    # Добавлены новые пути
    path('my-team/', views.my_team, name='my_team'),
    path('my-team/remove/<int:employee_id>/', views.remove_from_team, name='remove_from_team'),
    path('employee/<int:user_id>/edit/', views.edit_employee, name='edit_employee'),
    path('report/', views.generate_report, name='generate_report'),
    path('report/<int:employee_id>/', views.employee_report, name='employee_report'),
]