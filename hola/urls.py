from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Inicio y autenticación
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Principal y bibliotecario
    path('principal/', views.principal, name='principal'),
    path('bibliotecario/', views.vista_bibliotecario, name='bibliotecario'),

    # Libros
    path('libros/', views.libros_view, name='libros'),

    # Préstamos
    path('prestamos/', views.prestamos, name='prestamos'),  
    path('listaprestamos/', views.listaprestamos, name='listaprestamos'),
    path('prestamos/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('generar_multas/', views.generar_multas, name='generar_multas'),
    path('prestamos', views.prestamo_mensaje, name='prestamo_mensaje'),
    path('eliminar_prestamos/', views.eliminar_prestamos, name='eliminar_prestamos'),
    # Reservas
    path('reservas/', views.reservas, name='reservas'),
    path('reservas/lista/', views.lista_reservas, name='lista_reservas'),
    path('reservas/devuelto/<int:reserva_id>/', views.marcar_reserva_devuelto, name='marcar_devuelto'),

    # Usuarios
    path('registro/', views.registro, name='registro'),
    path('usuario/formulario/', views.usuario_formulario, name='usuario_formulario'),

    # Estadísticas
    path('estadisticas/', views.estadisticas, name='estadisticas'),

    # Otros
    path('contacto/', views.contacto, name='contacto'),
    path('galerialibro/', views.galerialibro, name='galerialibro'),
    path('escritores/', views.escritores, name='escritores'),
    path('redessociales/', views.redessociales, name='redessociales'),
    path('acercanosotros/', views.acerca, name='acerca'),
]
