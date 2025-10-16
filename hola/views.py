from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import PerfilForm
from datetime import date, timedelta
from django.http import HttpResponse
from django.contrib.auth import logout
from django.urls import reverse
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from .forms import PerfilForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from django.urls import reverse
from .models import Usuario, Libro, Prestamo, Reserva, Categoria, Autor, Multa, Notificacion
from .forms import (
    PrestamoForm,
    ReservaForm,
    LibroForm,
    UsuarioForm,
    BuscarLibroForm,
    CustomUserCreationForm
)

User = get_user_model()

# =========================
# LOGIN
# =========================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('principal')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'hola/login.html', {'form': form})




def logout_view(request):
    logout(request)  # Cierra la sesión
     # Redirige directamente al login
    return redirect(reverse('login'))


def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data['email']

            if Usuario.objects.filter(email=email).exists():
                messages.error(request, "Este email ya está registrado.")
            else:
                user.email = email
                user.save()
                Usuario.objects.create(
                    user=user,
                    nombre=user.username,
                    apellido='',
                    email=email,
                    tipo='lector'
                )
                messages.success(request, "Usuario registrado correctamente. Por favor inicia sesión.")
                return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'hola/registro.html', {'form': form})


# =========================
# HOME / PRINCIPAL
# =========================


def home(request):
    """
    Si el usuario está autenticado, va a 'principal'.
    Si no, redirige al login.
    """
    if request.user.is_authenticated:
        return redirect('principal')
    return redirect('login')


@login_required
def principal(request):
    # Asegurarse de que el usuario tenga perfil
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    usuario = Usuario.objects.filter(user=request.user).first()
    if not usuario:
        usuario = Usuario.objects.create(user=request.user, email=request.user.email, nombre=request.user.username, apellido='')
    return render(request, 'hola/principal.html', {'usuario': usuario, 'perfil': perfil})




# =========================
# USUARIO
# =========================
@login_required
def usuario_formulario(request):
    form = UsuarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Usuario creado correctamente")
        return redirect('usuario_formulario')
    return render(request, 'hola/usuario_formulario.html', {'form': form})

def es_bibliotecario(user):
    return user.groups.filter(name='Bibliotecario').exists()

@login_required
@user_passes_test(es_bibliotecario)
def vista_bibliotecario(request):
    return render(request, 'hola/bibliotecario.html', {'mensaje': 'Bienvenido Bibliotecario'})

# ========================@login_required
def libros_view(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    
    # Formulario completo solo para admin
    form = LibroForm(request.POST or None) if es_admin else None
    if request.method == 'POST' and es_admin and form.is_valid():
        form.save()
        messages.success(request, "Libro guardado correctamente.")
        return redirect('libros')

    # Formulario de búsqueda para todos
    buscar_form = BuscarLibroForm(request.GET or None)
    lista_libros = Libro.objects.all()

    if buscar_form.is_valid():
        titulo = buscar_form.cleaned_data.get('titulo')
        autor = buscar_form.cleaned_data.get('autor')
        categoria = buscar_form.cleaned_data.get('categoria')
        if titulo: lista_libros = lista_libros.filter(titulo__icontains=titulo)
        if autor: lista_libros = lista_libros.filter(autor=autor)
        if categoria: lista_libros = lista_libros.filter(categoria=categoria)

    # Marcar disponibilidad de cada libro
    for libro in lista_libros:
        libro.disponible = libro.ejemplares > 0

    return render(request, 'hola/libro.html', {
        'libros': lista_libros,
        'form': form,
        'buscar_form': buscar_form,
        'es_admin': es_admin
    })


# =========================
# PRÉSTAMOS
# =========================
@login_required
def prestamos(request):
    usuario_logueado = Usuario.objects.get(user=request.user)
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    form = PrestamoForm(request.POST or None, usuario_logueado=usuario_logueado)

    if request.method == 'POST' and form.is_valid():
        libro = form.cleaned_data['libro']
        if libro.ejemplares <= 0:
            messages.error(request, f"El libro '{libro.titulo}' no tiene ejemplares disponibles.")
            return redirect('prestamos')

        prestamo = form.save(commit=False)
        if not es_admin:
            prestamo.usuario = usuario_logueado
        prestamo.save()
        Libro.objects.filter(id=libro.id).update(ejemplares=F('ejemplares') - 1)
        messages.success(request, f"Préstamo del libro '{libro.titulo}' guardado correctamente.")
        form = PrestamoForm(usuario_logueado=usuario_logueado)

    return render(request, 'hola/prestamos.html', {'form': form, 'es_admin': es_admin})

@login_required
def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if prestamo.devuelto:
        messages.warning(request, "Este préstamo ya fue devuelto.")
        return redirect("lista_prestamos")

    prestamo.devuelto = True
    prestamo.fecha_devolucion = date.today()
    prestamo.libro.estado = "disponible"
    prestamo.libro.save()
    prestamo.save()

    retraso = (prestamo.fecha_devolucion - prestamo.fecha_limite).days
    if retraso > 0:
        monto = retraso * 100
        multa = Multa.objects.create(prestamo=prestamo, monto=monto)
        Notificacion.objects.create(usuario=prestamo.usuario, prestamo=prestamo,
            mensaje=f"Tienes una multa de ${monto} por devolver con {retraso} día(s) de retraso.")
        messages.error(request, f"Libro devuelto con retraso. Multa generada: ${monto}")
    else:
        Notificacion.objects.create(usuario=prestamo.usuario, prestamo=prestamo,
            mensaje="Has devuelto tu libro a tiempo. ¡Gracias!")
        messages.success(request, "Libro devuelto correctamente y sin multa.")

    return redirect("listaprestamos")

@login_required
def prestamo_mensaje(request):
    # Este mensaje puede venir de session o query string; para ejemplo fijo:
    mensaje = "No puedes tomar un nuevo libro, tienes multas pendientes."
    return render(request, 'prestamo_mensaje.html', {'mensaje': mensaje})


@login_required
def listaprestamos(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    prestamos = Prestamo.objects.all().select_related('usuario', 'libro').prefetch_related('multa_set')
    usuarios = Usuario.objects.all()
    libros = Libro.objects.all()
    return render(request, 'hola/listaprestamos.html', {
        'prestamos': prestamos,
        'es_admin': es_admin,
        'usuarios': usuarios,
        'libros': libros
    })

def limpiar_prestamos(request):
    if request.user.is_superuser:  # Solo superusuario puede limpiar
        Prestamo.objects.all().delete()
    return redirect('prestamos')  # Redirige a la página de préstamos




@login_required
def eliminar_prestamos(request):
    if request.method == "POST":
        ids = request.POST.getlist('prestamos_ids')
        user = request.user
        es_admin = user.is_superuser or user.groups.filter(name='Bibliotecario').exists()

        if es_admin:
            Prestamo.objects.filter(id__in=ids).delete()
        else:
            Prestamo.objects.filter(id__in=ids, usuario__user=user).delete()

    return redirect('listaprestamos')
# =========================
# RESERVAS
# =========================
@login_required
def reservas(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    if request.method == "POST":
        libro_id = request.POST.get("libro")
        libro = get_object_or_404(Libro, id=libro_id)
        usuario = None

        if es_admin:
            usuario_id = request.POST.get("usuario")
            if not usuario_id:
                messages.error(request, "Debe seleccionar un usuario para la reserva.")
                return redirect('reservas')
            usuario = get_object_or_404(Usuario, id=usuario_id)
        else:
            usuario = request.user.usuario

        if libro.ejemplares > 0:
            reserva = Reserva.objects.create(
                usuario=usuario,
                libro=libro,
                estado='activo',
                fecha_inicio=date.today(),
                fecha_fin=date.today() + timedelta(days=7)
            )
            libro.ejemplares -= 1
            libro.save()
            messages.success(request, f"Reserva del libro '{libro.titulo}' realizada correctamente.")
        else:
            reserva = Reserva.objects.create(usuario=usuario, libro=libro, estado='pendiente')
            messages.info(request,
                f"El libro '{libro.titulo}' está prestado/reservado y no está disponible por el momento. Se le avisará cuando esté disponible."
            )

        return redirect("mis_reservas")

    libros = Libro.objects.all()
    usuarios = Usuario.objects.all() if es_admin else [request.user.usuario]
    return render(request, "hola/reservas.html", {"libros": libros, "usuarios": usuarios, "es_admin": es_admin})


@login_required
def devolver_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    # Buscar si existe alguna reserva pendiente para este libro
    reserva_pendiente = Reserva.objects.filter(
        libro=libro, 
        estado='pendiente'
    ).order_by('fecha_inicio').first()

    # Marcar el libro como disponible
    libro.disponible = True
    libro.save()

    # Si hay reserva pendiente, activarla
    if reserva_pendiente:
        reserva_pendiente.estado = 'activo'
        reserva_pendiente.save()

    # ✅ Mostrar plantilla con confirmación
    messages.success(request, f"El libro '{libro.titulo}' fue devuelto correctamente.")
    
    return render(request, "hola/devolucion_exitosa.html", {"libro": libro})


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    instance.perfil.save()



@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user.usuario).select_related('libro').order_by('-fecha_inicio')
    return render(request, "hola/mis_reservas.html", {'reservas': reservas})



@login_required
def marcar_reserva_finalizado(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if reserva.estado != 'finalizado':
        reserva.estado = 'finalizado'
        reserva.save()
    return redirect('lista_reservas')

def limpiar_reserva(request, reserva_id):
    if request.method == 'POST':
        reserva = get_object_or_404(Reserva, id=reserva_id)
        reserva.delete()
        messages.success(request, "Reserva eliminada correctamente.")
    return redirect('lista_reservas')




def limpiar_todas_reservas(request):
    if request.method == 'POST':
        Reserva.objects.all().delete()  # borra todas las reservas
        messages.success(request, "Todas las reservas se han eliminado correctamente.")
   
    return redirect('lista_reservas')  # reemplaza con tu url de historial


def limpiar_reservas_finalizadas(request):
    if request.method == "POST":
        # Solo elimina las reservas con estado "finalizado"
        finalizadas = Reserva.objects.filter(estado='finalizado')
        count = finalizadas.count()
        finalizadas.delete()
        messages.success(request, f"{count} reservas finalizadas fueron eliminadas correctamente.")
    return redirect('reservas')

@login_required
def perfil_usuario(request):
    usuario_actual = Usuario.objects.get(user=request.user)
    reservas = Reserva.objects.filter(usuario=usuario_actual).select_related('libro').order_by('-fecha_inicio')
    for reserva in reservas:
        if reserva.estado == 'activo':
            reserva.mensaje = f'El libro "{reserva.libro.titulo}" ya está disponible para recoger.'
        elif reserva.estado == 'pendiente':
            reserva.mensaje = f'El libro "{reserva.libro.titulo}" aún no está disponible.'
        else:
            reserva.mensaje = None
    return render(request, 'hola/perfil_usuario.html', {'reservas': reservas})



@login_required
def editar_perfil(request):
    perfil = request.user.perfil  # tu modelo Perfil relacionado 1:1
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Foto de perfil actualizada ✅")
            return redirect('principal')
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, 'hola/editar_perfil.html', {'form': form})




@login_required
def lista_reservas(request):
    if request.user.is_superuser or es_bibliotecario(request.user):
        reservas = Reserva.objects.select_related('usuario', 'libro').order_by('-fecha_inicio')
        return render(request, 'hola/lista_reservas.html', {'reservas': reservas})
    messages.error(request, "No tienes permiso para ver esta página.")
    return redirect('principal')

# =========================
# INVENTARIO
# =========================
@login_required
def inventario_sgb(request):
    if not request.user.is_superuser:
        return redirect('principal')

    libros = Libro.objects.all()
    inventario = []
    for libro in libros:
        reservas_activas = Reserva.objects.filter(libro=libro, estado__in=['activo','pendiente']).count()
        disponible = max(libro.ejemplares - reservas_activas, 0)
        inventario.append({'libro': libro, 'total': libro.ejemplares, 'disponible': disponible, 'prestados': reservas_activas})

    return render(request, 'hola/inventario_sgb.html', {'inventario': inventario})

def contacto(request):
    return render(request, "hola/contacto.html")



def redessociales(request):
    return render(request, "hola/redessociales.html")

def galerialibro(request):
    # Si necesitas enviar los libros al template
    top_libros = Libro.objects.all()[:12]  # Ajusta según tu modelo
    return render(request, "hola/galerialibro.html", {"top_libros": top_libros})

def escritores(request):
    # Si necesitas enviar autores al template
    top_autores = Autor.objects.all()[:12]  # Ajusta según tu modelo
    return render(request, "hola/escritores.html", {"top_autores": top_autores})

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data['email']

            if Usuario.objects.filter(email=email).exists():
                messages.error(request, "Este email ya está registrado.")
            else:
                user.email = email
                user.save()
                Usuario.objects.create(
                    user=user,
                    nombre=user.username,
                    apellido='',
                    email=email,
                    tipo='lector'
                )
                messages.success(request, "Usuario registrado correctamente. Por favor inicia sesión.")
                return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'hola/registro.html', {'form': form})


def estadisticas(request):
    # Top 5 libros más prestados
    top_prestados = (
        Prestamo.objects.values("libro__titulo")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # Top 5 libros más reservados
    top_reservados = (
        Reserva.objects.values("libro__titulo")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # Total de préstamos
    total_prestamos = Prestamo.objects.count()

    # Usuarios activos
    usuarios_activos = Usuario.objects.count()

    # Evolución de préstamos por día
    prestamos_por_dia = (
        Prestamo.objects.annotate(dia=TruncDate("fecha_prestamo"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("dia")
    )

    return render(request, "hola/reportesestadisticas.html", {
        "top_prestados": top_prestados,
        "top_reservados": top_reservados,
        "total_prestamos": total_prestamos,
        "usuarios_activos": usuarios_activos,
        "prestamos_por_dia": prestamos_por_dia,
    })


def generar_multas(request):
    prestamos_vencidos = Prestamo.objects.filter(devuelto=False, fecha_limite__lt=date.today())

    for prestamo in prestamos_vencidos:
        retraso = (date.today() - prestamo.fecha_limite).days
        if retraso > 0:
            # Crear o actualizar la multa según días de retraso
            multa, created = Multa.objects.get_or_create(prestamo=prestamo)
            multa.monto = retraso * 100  # ajusta según tu regla
            multa.save()

            # Crear o actualizar notificación
            noti, _ = Notificacion.objects.get_or_create(
                usuario=prestamo.usuario,
                prestamo=prestamo,
            )
            noti.mensaje = f"Tienes una multa de ${multa.monto} por el libro '{prestamo.libro.titulo}'."
            noti.save()

    return HttpResponse("Multas y notificaciones generadas ✅")

def acerca(request):
    return render(request, 'hola/acercanosotros.html')



def sitemap_html(request):
    return render(request, 'hola/sitemap.html')





# Vista para mostrar la imagen
def imagen(request):
    return render(request, 'sandia.html')


def enviar_notificacion_multa(request, multa_id):
    try:
        multa = Multa.objects.get(id=multa_id)
        usuario = multa.prestamo.usuario
        libro = multa.prestamo.libro

        mensaje = (
            f"Hola {usuario.nombre},\n\n"
            f"Tienes una multa de ${multa.monto} "
            f"por devolver tarde el libro '{libro.titulo}'.\n"
            f"Por favor, regulariza tu situación lo antes posible.\n\n"
            "Gracias."
        )

        send_mail(
            subject='Notificación de Multa',
            message=mensaje,
            from_email='felixromanlebron24@gmail.com',   # tu correo remitente
            recipient_list=[usuario.email],    # correo del usuario
            fail_silently=False,
        )
        return HttpResponse("Correo enviado correctamente ✅")
    except Multa.DoesNotExist:
        return HttpResponse("❌ Multa no encontrada")


def root_redirect(request):
    return redirect('/login/')