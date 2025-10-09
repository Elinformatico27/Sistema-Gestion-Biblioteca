from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Inicio y autenticación
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    
    # Principal y bibliotecario
    path('principal/', views.principal, name='principal'),
    path('bibliotecario/', views.vista_bibliotecario, name='bibliotecario'),

    # Libros
    path('libros/', views.libros_view, name='libros'),

    # Préstamos
    path('listaprestamos/', views.listaprestamos, name='listaprestamos'),
    path('generar_multas/', views.generar_multas, name='generar_multas'),
    path('prestamos/', views.prestamos, name='prestamos'),
    path('prestamo/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('reserva/finalizar/<int:reserva_id>/', views.marcar_reserva_finalizado, name='marcar_reserva_finalizado'),
    path('lista_reservas/', views.lista_reservas, name='lista_reservas'),
    path('prestamo_mensaje/', views.prestamo_mensaje, name='prestamo_mensaje'),
    path('prestamos/limpiar/', views.limpiar_prestamos, name='limpiar_prestamos'),
    

    # Usuarios
    path('registro/', views.registro, name='registro') ,
    path('reservas/', views.reservas, name='reservas'),
    path('usuario/formulario/', views.usuario_formulario, name='usuario_formulario'),  
    path('prestamos/crear/', views.prestamos, name='crear_prestamo'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('contacto/', views.contacto, name='contacto'),
    path('galerialibro/', views.galerialibro, name='galerialibro'),
    path('escritores/', views.escritores, name='escritores'),
    path('redessociales/', views.redessociales, name='redessociales'),
    path('acercanosotros/', views.acerca, name='acerca'),
     path('sandia/', views.ver_sandia, name='ver_sandia'),
] 

