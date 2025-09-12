from django.db import models
from django.conf import settings

# Роли
ROLE_CHOICES = (
    ('employee', 'Сотрудник'),
    ('manager', 'Начальник отдела'),
    ('director', 'Генеральный директор'),
)

# Изменен порядок полей и добавлены новые
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    surname = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отчество')
    position = models.CharField("Должность", max_length=100, blank=True)
    phone_internal = models.CharField("Внутренний номер", max_length=10, blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/',
                              blank=True,
                              verbose_name='Фото')
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='employee')
    # Добавлено поле для связи: кто начальник у этого сотрудника
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates',
                                verbose_name="Начальник")
    def __str__(self):
        return f'Profile of {self.user.username}'
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'