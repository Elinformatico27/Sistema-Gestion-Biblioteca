# hola/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Usuario, Libro, Prestamo, Reserva, Categoria, Autor
from datetime import date
from .models import Perfil

# -----------------------------
# Formulario de Usuario
# -----------------------------
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
        }

# -----------------------------
# Formulario de Libro
# -----------------------------
from django import forms
from .models import Libro, Categoria, Editorial, Etiqueta, Autor

class LibroForm(forms.ModelForm):
    autor_nombre = forms.CharField(
        label="Autor",
        max_length=100,
        required=True,
        help_text="Escribe el nombre del autor. Si no existe, se creará automáticamente."
    )

    class Meta:
        model = Libro
        fields = ['titulo', 'isbn', 'autor_nombre', 'categoria', 'editorial', 'fecha_publicacion', 'paginas', 'ejemplares', 'estado', 'etiquetas']
        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'editorial': forms.Select(attrs={'class': 'form-select'}),
            'etiquetas': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        # Primero obtenemos o creamos el autor
        autor_nombre = self.cleaned_data.pop('autor_nombre')
        autor_obj, _ = Autor.objects.get_or_create(nombre=autor_nombre)
        self.instance.autor = autor_obj
        return super().save(commit=commit)


# -----------------------------
# Formulario de Préstamo
# -----------------------------

# -----------------------------
# Formulario de Préstamo
# -----------------------------
from django import forms
from .models import Prestamo, Libro, Usuario

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['usuario', 'libro', 'fecha_limite']
        widgets = {
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'libro': forms.Select(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, usuario_logueado=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostrar solo libros realmente disponibles
        libros_disponibles = [libro.id for libro in Libro.objects.all() if libro.disponible_real > 0]
        self.fields['libro'].queryset = Libro.objects.filter(id__in=libros_disponibles)

        # Configuración de usuario
        if usuario_logueado is None:
            self.fields['usuario'].queryset = Usuario.objects.none()
            return

        es_admin = (
            usuario_logueado.user.is_superuser or
            usuario_logueado.user.groups.filter(name='Bibliotecario').exists()
        )

        if es_admin:
            self.fields['usuario'].queryset = Usuario.objects.all()
        else:
            self.fields['usuario'].queryset = Usuario.objects.filter(pk=usuario_logueado.pk)
            self.fields['usuario'].initial = usuario_logueado
            self.fields['usuario'].disabled = True



# Formulario de Reserva

from django.core.exceptions import ValidationError


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'libro', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'libro': forms.Select(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, usuario_logueado=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostrar solo libros disponibles
        libros_disponibles = [libro.id for libro in Libro.objects.all() if libro.disponible_real > 0]
        self.fields['libro'].queryset = Libro.objects.filter(id__in=libros_disponibles)

        # Configuración de usuario
        if usuario_logueado:
            es_admin = usuario_logueado.user.is_superuser or usuario_logueado.user.groups.filter(name='Bibliotecario').exists()
            if es_admin:
                self.fields['usuario'].queryset = Usuario.objects.all()
            else:
                self.fields['usuario'].queryset = Usuario.objects.filter(pk=usuario_logueado.pk)
                self.fields['usuario'].initial = usuario_logueado
                self.fields['usuario'].disabled = True
        else:
            self.fields['usuario'].queryset = Usuario.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio < date.today():
                raise ValidationError("La fecha de inicio no puede ser anterior a hoy.")
            if fecha_fin < fecha_inicio:
                raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")


# Registro de Usuario
# -----------------------------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

# -----------------------------
# Búsqueda de libros
# -----------------------------
class BuscarLibroForm(forms.Form):
    titulo = forms.CharField(
        required=False, 
        label="Título",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    autor = forms.ModelChoiceField(
        queryset=Autor.objects.all(),
        required=False,
        empty_label="Todos los autores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )



class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['avatar']
