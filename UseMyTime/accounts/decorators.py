from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def role_required(allowed_roles):
    """
    Декоратор: доступ только для указанных ролей.
    Пример: @role_required(['manager', 'director'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Сначала проверяем, авторизован ли пользователь
            if not request.user.is_authenticated:
                return redirect('login')

            try:
                # Предполагаем, что у пользователя есть профиль с полем `role`
                profile = request.user.profile
                if profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return redirect('index')
            except AttributeError:
                # Если у пользователя нет профиля
                return redirect('index')
        return _wrapped_view
    return decorator