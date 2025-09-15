from django.apps import AppConfig
from django.db.models.signals import post_migrate

# Создание тестовых данных
def create_test_data(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.filter(username='root').delete()
    user = User.objects.create_superuser('root', 'root@example.com', 'root')

    from contacts.models import Contact
    Contact.objects.all().delete()
    Contact.objects.create(last_name='Паршаков',
                            first_name='Вячеслав',
                            surname='Владимирович',
                            position='Разработчик',
                            email='parsakovslava03@gmail.com',
                            phone='89133627577')
    
    from accounts.models import Profile
    Profile.objects.create(user=user)

    from work_programs.models import WorkProgram
    WorkProgram.objects.all().delete()
    WorkProgram.objects.bulk_create([
        WorkProgram(name='Mathcad'),
        WorkProgram(name='AutoCAD'),
        WorkProgram(name='Adobe Photoshop'),
        WorkProgram(name='Adobe Acrobat'),
        WorkProgram(name='Компас')
    ])

class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    
    # Выполнение создания тестовых данных
    def ready(self):
        #post_migrate.connect(create_test_data, sender=self)
        pass