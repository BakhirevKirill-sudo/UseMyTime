from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Форма для регистрации
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повтор пароля',
                                widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    # Валидация пароля
    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password, self.instance)
        except ValidationError as error:
            self.add_error('password', error)
        return password

    # Проверка совпадения паролей
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']

    # Проверка уникальности почты
    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Эта почта занята')
        return data

# Форма редактирования пользователя
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    # Проверка уникальности почты
    def clean_email(self):
        data = self.cleaned_data['email']
        qs = User.objects.exclude(id=self.instance.id)\
                         .filter(email=data)
        if qs.exists():
            raise forms.ValidationError('Эта почта занята')
        return data

# Форма редактирования профиля
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo', 'surname', 'position', 'phone_internal'] # Изменены используемые поля