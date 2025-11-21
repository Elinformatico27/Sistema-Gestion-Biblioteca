from django.contrib import admin
from hola.models import Multa, Notificacion
from .models import (
    Libro,
    Etiqueta,
    Categoria,
    Autor,
    Editorial,
    Usuario,
    Prestamo,
    Reserva,
)

# ===========================
# Autor Admin
# ===========================
@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'libros_info')
    search_fields = ('nombre',)

    def libros_info(self, obj):
        libros = Libro.objects.filter(autor=obj)
        return ", ".join([
            f"{libro.titulo} | ISBN: {libro.isbn} | Categoría: {libro.categoria} | Fecha: {libro.fecha_publicacion} | Estado: {libro.estado}" 
            for libro in libros
        ])
    libros_info.short_description = "Libros del Autor"

# ===========================
# Libro Admin
# ===========================
@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'isbn', 'categoria', 'editorial', 'fecha_publicacion', 'estado', 'ejemplares')
    list_filter = ('estado', 'categoria', 'editorial')
    search_fields = ('titulo', 'autor__nombre', 'isbn')

# ===========================
# Categoria Admin
# ===========================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

# ===========================
# Editorial Admin
# ===========================
@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais')
    search_fields = ('nombre', 'pais')

# ===========================
# Usuario Admin
# ===========================
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'tipo', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('tipo',)

# ===========================
# Prestamo Admin
# ===========================
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'libro', 'fecha_prestamo', 'fecha_limite', 'fecha_devolucion', 'devuelto')
    list_filter = ('devuelto',)
    search_fields = ('usuario__nombre', 'libro__titulo')

# ===========================
# Reserva Admin
# ===========================
from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'libro', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('usuario__nombre', 'libro__titulo')
    fields = ('usuario', 'libro', 'fecha_inicio', 'fecha_fin', 'estado')  # Todos editables
    autocomplete_fields = ['usuario', 'libro']  # útil si hay muchos registros


# ===========================
# Multa Admin
# ===========================
@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('monto', 'fecha')
    list_filter = ('fecha',)

# ===========================
# Notificacion Admin
# ===========================
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensaje', 'fecha')
    search_fields = ('usuario__nombre', 'mensaje')
