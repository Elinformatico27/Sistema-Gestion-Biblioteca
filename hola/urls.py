from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # ----------------------
    # Inicio y autenticación
    # ----------------------
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    # ----------------------
    # Principal y bibliotecario
    # ----------------------
    path('principal/', views.principal, name='principal'),
    path('bibliotecario/', views.vista_bibliotecario, name='bibliotecario'),

    # ----------------------
    # Libros
    # ----------------------
    path('libros/', views.libros_view, name='libros'),

    # ----------------------
    # Préstamos
    # ----------------------
    path('prestamos/', views.prestamos, name='prestamos'),
    path('listaprestamos/', views.listaprestamos, name='listaprestamos'),
    path('prestamo/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('prestamo_mensaje/', views.prestamo_mensaje, name='prestamo_mensaje'),
    path('prestamos/limpiar/',views.eliminar_prestamos, name='limpiar_prestamos'),
    path('prestamos/crear/', views.prestamos, name='crear_prestamo'),

    # ----------------------
    # Reservas
    # ----------------------
    path('reservas/', views.reservas, name='reservas'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('lista_reservas/', views.lista_reservas, name='lista_reservas'),
    path('reserva/finalizar/<int:reserva_id>/', views.marcar_reserva_finalizado, name='marcar_reserva_finalizado'),
    path('reservas/eliminar/<int:reserva_id>/', views.limpiar_reserva, name='limpiar_reserva'),
    path('limpiar_reservas/', views.limpiar_reserva, name='limpiar_reservas'),
    path('limpiar_todas_reservas/', views.limpiar_todas_reservas, name='limpiar_todas_reservas'),
    path('limpiar_reservas_finalizadas/', views.limpiar_reservas_finalizadas, name='limpiar_reservas_finalizadas'),
    path('perfil_usuario/', views.perfil_usuario, name='perfil_usuario'),
    path('inventario_sgb/', views.inventario_sgb, name='inventario_sgb'),
    # ----------------------
    # Usuarios
    # ----------------------
    path('registro/', views.registro, name='registro'),
    path('usuario/formulario/', views.usuario_formulario, name='usuario_formulario'),

    # ----------------------
    # Estadísticas y extras
    # ----------------------
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('generar_multas/', views.generar_multas, name='generar_multas'),
    path('contacto/', views.contacto, name='contacto'),
    path('galerialibro/', views.galerialibro, name='galerialibro'),
    path('escritores/', views.escritores, name='escritores'),
    path('redessociales/', views.redessociales, name='redessociales'),
    path('acercanosotros/', views.acerca, name='acerca'),
    path('libro/devolver/<int:libro_id>/', views.devolver_libro, name='devolver_libro'),
    path('sitemap/', views.sitemap_html, name='sitemap'),




    path('sandia/', views.imagen, name='imagen'),
    path('enviar-notificacion-multa/<int:multa_id>/', views.enviar_notificacion_multa, name='enviar_notificacion_multa'),

   # path('enviar-multa-prueba/', views.enviar_notificacion_multa, name='enviar_notificacion_multa'),
    path('', views.home, name='home'),   # raíz
    
 

]

    
    

