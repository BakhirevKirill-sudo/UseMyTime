from django.db import models
from django.conf import settings
from work_programs.models import WorkProgram
from datetime import timedelta

# Модель проектов
class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='projects')
    title = models.CharField(max_length=200, verbose_name='Название проекта')
    description = models.TextField(verbose_name='Описание проекта')
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    total_time = models.DurationField(default=timedelta(0))
    programs = models.ManyToManyField(
        WorkProgram,
        through='ProjectProgram',
        through_fields=['project', 'program']
    )

    def get_hours_minutes_seconds(self):
        seconds = int(self.total_time.total_seconds())
        return [seconds // 3600, (seconds % 3600) // 60, seconds]  # [hours, minutes, seconds]

# Промежуточная модель между программами и проектами
# Хранит время работы над проектом для каждой программы
class ProjectProgram(models.Model):
    program = models.ForeignKey(WorkProgram, 
                                on_delete=models.CASCADE,
                                related_name='project_programs')
    project = models.ForeignKey(Project, 
                                on_delete=models.CASCADE,
                                related_name='project_programs')
    total_time = models.DurationField(default=timedelta(0))

    def get_hours_minutes_seconds(self):
        seconds = int(self.total_time.total_seconds())
        return [seconds // 3600, (seconds % 3600) // 60, seconds] # [hours, minutes, seconds]

# Модель активного проекта
# Для него и будет учитываться время
class ActiveProject(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='active_project')
    project = models.ForeignKey(Project, 
                                on_delete=models.CASCADE, 
                                null=True, blank=True)
    current_program = models.ForeignKey(WorkProgram,
                                        on_delete=models.SET_NULL,
                                        null=True, blank=True)
    in_work = models.BooleanField(default=False)
    last_started_at = models.DateTimeField(auto_now=True)

# Модель подзадач проекта
class Task(models.Model):
    project = models.ForeignKey(Project, 
                                on_delete=models.CASCADE,
                                related_name='tasks')
    text = models.TextField(verbose_name='Текст задачи')
    is_done = models.BooleanField(default=False, verbose_name='Выполнено')
    created_at = models.DateTimeField(auto_now_add=True)