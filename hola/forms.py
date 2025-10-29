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
class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = '__all__'
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'editorial': forms.Select(attrs={'class': 'form-control'}),
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'paginas': forms.NumberInput(attrs={'class': 'form-control'}),
            'ejemplares': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn', '').replace('-', '').strip()
        if not isbn.isdigit() or len(isbn) != 13:
            raise forms.ValidationError("El ISBN debe tener exactamente 13 dígitos numéricos.")
        return isbn

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
