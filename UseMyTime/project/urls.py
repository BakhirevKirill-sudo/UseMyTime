from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('accounts.urls')),
    path('contacts/', include('contacts.urls')),
    path('programs/', include('work_programs.urls')),
    path('projects/', include('projects.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='index')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)