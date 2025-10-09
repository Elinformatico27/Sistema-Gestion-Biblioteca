# hola/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Usuario, Libro, Prestamo, Reserva, Categoria, Autor
from datetime import date

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


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['usuario', 'libro', 'fecha_limite']

    def __init__(self, *args, usuario_logueado=None, **kwargs):
        super().__init__(*args, **kwargs)

        if usuario_logueado is None:
            # Por seguridad, si no llega usuario logueado
            self.fields['usuario'].queryset = Usuario.objects.none()
            return

        # Determinar si es admin / bibliotecario
        es_admin = usuario_logueado.user.is_superuser or usuario_logueado.user.groups.filter(name='Bibliotecario').exists()

        if es_admin:
            # Admin ve todos los usuarios
            self.fields['usuario'].queryset = Usuario.objects.all()
        else:
            # Usuario normal solo puede verse a sí mismo
            self.fields['usuario'].queryset = Usuario.objects.filter(pk=usuario_logueado.pk)
            self.fields['usuario'].initial = usuario_logueado








# Formulario de Reserva
# ----------------# hola/forms.py
from django import forms
from .models import Reserva, Usuario, Libro

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'libro', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        usuario_logueado = kwargs.pop('usuario', None)  # objeto Usuario logueado
        super().__init__(*args, **kwargs)

        # Mostrar solo libros disponibles
        self.fields['libro'].queryset = Libro.objects.filter(estado='disponible')

        if usuario_logueado:
            if usuario_logueado.tipo == 'admin':
                # Admin: mostrar todos los usuarios
                self.fields['usuario'].queryset = Usuario.objects.all()
                self.fields['usuario'].disabled = False
            else:
                # Usuario normal: solo mostrar su propio usuario
                self.fields['usuario'].queryset = Usuario.objects.filter(id=usuario_logueado.id)
                self.fields['usuario'].initial = usuario_logueado
                self.fields['usuario'].disabled = True









# -----------------------------
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
