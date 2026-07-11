from django import forms
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(render_value=False, attrs={'class': 'form-control'}),
        required=False,
        help_text='Dejar vacío para mantener la actual al editar',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'groups']
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'is_active': 'Estado Activo',
            'groups': 'Roles Asignados',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password'].help_text = 'La contraseña es obligatoria para crear el usuario.'

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename'),
        widget=forms.SelectMultiple(attrs={'size': 20, 'class': 'form-select'}),
        required=False,
        label='Permisos Asignados',  
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nombre del Rol',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'permissions' in self.fields:
            choices = []
            for pk, label in self.fields['permissions'].choices:
                
                label = label.replace('Security', 'Seguridad')
                label = label.replace('Core', 'Principal')
                label = label.replace('Sesiones', 'Sesiones')
                label = label.replace('Autenticación y autorización', 'Autenticación')
                label = label.replace('Tipos de contenido', 'Tipos de Contenido')
                
                label = label.replace('Can add', 'Puede añadir')
                label = label.replace('Can change', 'Puede modificar')
                label = label.replace('Can delete', 'Puede eliminar')
                label = label.replace('Can view', 'Puede ver')
                
                label = label.replace('log entry', 'entrada de registro')
                label = label.replace('group', 'rol / grupo')
                label = label.replace('permission', 'permiso')
                label = label.replace('content type', 'tipo de contenido')
                label = label.replace('usuario', 'usuario')
                label = label.replace('Elemento de menú', 'elemento de menú')
                label = label.replace('session', 'sesión')
                
                choices.append((pk, label))
            self.fields['permissions'].choices = choices

class ProfileForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'foto']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este email ya está registrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if p1:
            validate_password(p1, self.instance)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
