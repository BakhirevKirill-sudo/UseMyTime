from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile
from django.contrib import messages

# Добавлены библиотеки
from projects.models import Project, Task
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML # Библиотека для формирования отчетов
from .decorators import role_required # Кастомный декоратор для проверки роли пользователя

# Отображение профиля
@login_required
def profile(request):
    return render(request,
                  'accounts/profile.html',
                  {'section': 'profile'})

# Регистрация пользователя
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(
                user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request,
                          'accounts/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request,
                  'accounts/register.html',
                  {'user_form': user_form})

# Редактирование данных пользователя
@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
                                    instance=request.user.profile,
                                    data=request.POST,
                                    files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile') # Исправлено (теперь после редактирования профиля пользователя перенаправляет обратно на страницу его профиля)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(
                                    instance=request.user.profile)
    return render(request,
                  'accounts/edit.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})

# Добавлена страница отдела для начальников
@login_required
@role_required(['manager'])
def my_team(request):
    profile = request.user.profile

    # Все подчинённые (кто имеет этого пользователя как manager)
    team = profile.subordinates.all()

    # Собираем задачи для каждого сотрудника
    team_tasks = []
    for employee in team:
        # Находим все проекты, где employee.user — владелец
        employee_projects = Project.objects.filter(user=employee.user, is_archived=False)
        # Находим все задачи из этих проектов
        tasks = Task.objects.filter(project__in=employee_projects)

        team_tasks.append({
            'employee': employee,
            'tasks': tasks
        })

    # Все доступные сотрудники: без начальника, не manager/director, и НЕ is_staff / is_superuser
    available_employees = Profile.objects.filter(manager__isnull=True).exclude(
        role__in=['manager', 'director']
    ).exclude(
        user__is_staff=True  # исключаем админов
    ).exclude(
        user__is_superuser=True  # исключаем суперпользователей
    )

    if request.method == "POST":
        employee_id = request.POST.get('employee_id')
        if employee_id:
            employee = get_object_or_404(Profile, id=employee_id)
            if employee.user.is_staff or employee.user.is_superuser:
                messages.error(request, "Нельзя добавить администратора в команду.")
            else:
                employee.manager = profile
                employee.save()
                messages.success(request, f"{ employee.user.last_name } { employee.user.first_name } ({ employee.position }) добавлен(а) в вашу команду.")
            return redirect('my_team')

    context = {
        'team_tasks': team_tasks,
        'available_employees': available_employees,
    }
    return render(request, 'accounts/my_team.html', context)

# Добавлена возможность убирать сотрудников из отдела
@login_required
@role_required(['manager'])
def remove_from_team(request, employee_id):
    profile = request.user.profile
    employee = get_object_or_404(Profile, id=employee_id)

    # Проверка: сотрудник действительно в подчинении
    if employee.manager == profile:
        employee.manager = None
        employee.save()
        messages.success(request, f"{ employee.user.last_name } { employee.user.first_name } ({ employee.position }) удалён из вашей команды.")
    else:
        messages.error(request, "Этот сотрудник не в вашей команде.")

    return redirect('my_team')

# Добавлена возможность редактировать профили добалвенных сотрудников
@login_required
@role_required(['manager'])
def edit_employee(request, user_id):
    """Редактирование профиля сотрудника (только для своего отдела)"""
    user = User.objects.get(id=user_id)
    profile = request.user.profile

    # Проверяем, что сотрудник в подчинении
    if user.profile.manager != profile and profile.role != 'director':
        messages.error(request, "Нет доступа.")
        return redirect('my_team')

    if request.method == 'POST':
        user_form = UserEditForm(instance=user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=user.profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"Профиль { user.last_name } { user.first_name } ({ user.profile.position }) успешно обновлён.")
            return redirect('my_team')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(
            instance=user.profile)

    return render(request, 'accounts/edit.html', {'user_form': user_form,
                   'profile_form': profile_form})

# Добавлена возможность генерировать отчет по всему отделу
@login_required
#@role_required(['manager'])
def generate_report(request):
    profile = request.user.profile
    team = Profile.objects.filter(manager=profile)

    team_report = []
    total_department_time = 0
    total_department_tasks = 0

    for employee in team:
        user = employee.user

        # Только неархивные проекты
        projects = Project.objects.filter(user=user, is_archived=False)
        completed_tasks = Task.objects.filter(
            project__in=projects,
            is_done=True
        ).select_related('project')

        employee_data = {
            'employee': employee,
            'project_data': [],
            'total_hours': 0,
            'total_minutes': 0,
            'total_tasks': completed_tasks.count()
        }

        total_seconds = 0

        for project in projects:
            tasks = completed_tasks.filter(project=project)
            if tasks.exists():
                proj_seconds = int(project.total_time.total_seconds())
                total_seconds += proj_seconds
                hours, minutes, seconds = project.get_hours_minutes_seconds()

                # Дата завершения — дата последней выполненной задачи
                last_task = tasks.order_by('-created_at').first()

                employee_data['project_data'].append({
                    'project': project,
                    'tasks': tasks,
                    'hours': hours,
                    'minutes': minutes,
                    'seconds': seconds,
                    'created_at': project.created_at,
                    'completed_at': last_task.created_at,
                })

        # Общее время по сотруднику
        employee_data['total_hours'] = total_seconds // 3600
        employee_data['total_minutes'] = (total_seconds % 3600) // 60
        employee_data['total_seconds'] = total_seconds % 60
        total_department_time += total_seconds
        total_department_tasks += employee_data['total_tasks']

        team_report.append(employee_data)

    # Общее время по отделу
    dept_total_hours = total_department_time // 3600
    dept_total_minutes = (total_department_time % 3600) // 60

    context = {
        'manager': profile,
        'team_report': team_report,
        'dept_total_hours': dept_total_hours,
        'dept_total_minutes': dept_total_minutes,
        'dept_total_tasks': total_department_tasks,
        'dept_total_seconds': total_department_time % 60,
        'now': timezone.now(),
    }

    # Если запрос на PDF
    if request.GET.get('format') == 'pdf':
        html_string = render_to_string('accounts/team_report.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        result = html.write_pdf()

        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="отчет_{employee.user.last_name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        return response

    return render(request, 'accounts/team_report.html', context)

# Добавлена возможность генерировать отчет по каждому сотруднику отдельно
@login_required
#@role_required(['manager'])
def employee_report(request, employee_id):
    # Получаем сотрудника
    employee = get_object_or_404(Profile, id=employee_id)
    user = employee.user

    # Только неархивные проекты
    projects = Project.objects.filter(user=user, is_archived=False)

    # Только выполненные задачи
    completed_tasks = Task.objects.filter(
        project__in=projects,
        is_done=True
    ).select_related('project')

    # Подготовка данных: группировка по проектам
    report_data = []
    total_time_seconds = 0

    for project in projects:
        tasks = completed_tasks.filter(project=project)
        if tasks.exists():
            hours, minutes, seconds = project.get_hours_minutes_seconds()  # [ч, м]
            total_time_seconds += int(project.total_time.total_seconds())

            report_data.append({
                'project': project,
                'tasks': tasks,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'created_at': project.created_at,
                # Завершение — дата последней выполненной задачи
                'completed_at': tasks.order_by('-created_at').first().created_at,
            })

    # Общее время
    total_hours = total_time_seconds // 3600
    total_minutes = (total_time_seconds % 3600) // 60

    context = {
        'employee': employee,
        'report_data': report_data,
        'completed_tasks': completed_tasks,
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'total_seconds': total_time_seconds,
        'now': timezone.now(),
    }

    # Если запрос на PDF
    if request.GET.get('format') == 'pdf':
        html_string = render_to_string('accounts/employee_report.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        result = html.write_pdf()

        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="отчет_{employee.user.last_name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        return response

    return render(request, 'accounts/employee_report.html', context)