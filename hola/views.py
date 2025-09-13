# views.py
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, F
from django.db.models.functions import TruncDate


from .models import Prestamo, Reserva, Usuario, Libro, Autor, Multa, Notificacion
from .forms import (
    PrestamoForm,
    ReservaForm,
    LibroForm,
    UsuarioForm,
    BuscarLibroForm,
    CustomUserCreationForm
)



# =========================
# FUNCIONES DE UTILIDAD
# =========================
def es_bibliotecario(user):
    return user.groups.filter(name='Bibliotecario').exists()


# =========================
# LOGIN Y REGISTRO
# =========================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('principal')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'hola/login.html', {'form': form})


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
                Usuario.objects.create(user=user, nombre=user.username, apellido='', email=email, tipo='lector')
                messages.success(request, "Usuario registrado correctamente. Por favor inicia sesión.")
                return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'hola/registro.html', {'form': form})


# =========================
# HOME / PRINCIPAL
# =========================
@login_required
def principal(request):
    usuario = Usuario.objects.filter(user=request.user).first()
    if not usuario:
        try:
            usuario = Usuario.objects.create(user=request.user, email=request.user.email)
        except Exception:
            messages.error(request, "No se pudo crear el usuario automáticamente.")
            return redirect('logout')
    return render(request, 'hola/principal.html', {'usuario': usuario})


def home(request):
    return render(request, 'hola/home.html')


# =========================
# USUARIOS
# =========================
@login_required
def usuario_formulario(request):
    form = UsuarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Usuario creado correctamente")
        return redirect('usuario_formulario')
    return render(request, 'hola/usuario_formulario.html', {'form': form})


@login_required
@user_passes_test(es_bibliotecario)
def vista_bibliotecario(request):
    return render(request, 'hola/bibliotecario.html', {'mensaje': 'Bienvenido Bibliotecario'})


# =========================
# LIBROS
# =========================
@login_required
def libros_view(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    form = LibroForm(request.POST or None) if es_admin else None

    if request.method == 'POST' and es_admin and form.is_valid():
        form.save()
        return redirect('libros')

    buscar_form = BuscarLibroForm(request.GET or None)
    lista_libros = Libro.objects.all()

    if buscar_form.is_valid():
        if buscar_form.cleaned_data.get('titulo'):
            lista_libros = lista_libros.filter(titulo__icontains=buscar_form.cleaned_data['titulo'])
        if buscar_form.cleaned_data.get('autor'):
            lista_libros = lista_libros.filter(autor=buscar_form.cleaned_data['autor'])
        if buscar_form.cleaned_data.get('categoria'):
            lista_libros = lista_libros.filter(categoria=buscar_form.cleaned_data['categoria'])

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

    if request.method == 'POST':
        form = PrestamoForm(request.POST, usuario_logueado=usuario_logueado)
        if form.is_valid():
            libro = form.cleaned_data['libro']
            if libro.ejemplares <= 0:
                messages.error(request, f"El libro '{libro.titulo}' no tiene ejemplares disponibles.")
                return redirect('prestamos')
            
            prestamo = form.save(commit=False)
            if not es_admin:
                prestamo.usuario = usuario_logueado
            prestamo.save()

            # Disminuir ejemplares
            Libro.objects.filter(id=libro.id).update(ejemplares=F('ejemplares') - 1)

            # 🚀 Enviar correo de confirmación
            asunto = "Confirmación de Préstamo"
            mensaje = f"Estimado {prestamo.usuario.nombre}, se le ha prestado el libro '{libro.titulo}' con fecha límite {prestamo.fecha_limite}."
            messages.success(request, f"Préstamo del libro '{libro.titulo}' guardado correctamente.")
            form = PrestamoForm(usuario_logueado=usuario_logueado)
        else:
            messages.error(request, "Error al guardar el préstamo. Verifique los campos.")
    else:
        form = PrestamoForm(usuario_logueado=usuario_logueado)

    return render(request, 'hola/prestamos.html', {'form': form, 'es_admin': es_admin})


@login_required
def devolver_prestamo(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    libro = prestamo.libro

    if prestamo.devuelto:
        messages.warning(request, "Este préstamo ya estaba devuelto.")
        return redirect('listaprestamos')

    prestamo.devuelto = True
    prestamo.fecha_devolucion = date.today()
    prestamo.save()

    # Aumentar ejemplares
    libro.ejemplares += 1
    libro.estado = 'disponible' if libro.ejemplares > 0 else 'no disponible'
    libro.save()

    # Calcular retraso
    retraso = (date.today() - prestamo.fecha_limite).days if prestamo.fecha_limite else 0

    if retraso > 0:
        monto_multa = retraso * 100
        Multa.objects.create(prestamo=prestamo, monto=monto_multa)
        Notificacion.objects.create(
            usuario=prestamo.usuario,
            prestamo=prestamo,
            mensaje=f"Tu préstamo del libro '{libro.titulo}' tuvo {retraso} días de retraso. Multa: ${monto_multa}."
        )
        # 🚀 Enviar correo
        asunto = "Multa por devolución atrasada"
        mensaje = f"Estimado {prestamo.usuario.nombre}, su préstamo del libro '{libro.titulo}' tuvo {retraso} días de retraso. Multa: ${monto_multa}."
        enviar_notificacion(prestamo.usuario, asunto, mensaje)
        messages.error(request, f"Libro devuelto con retraso. Multa generada: ${monto_multa}.")
    else:
        Notificacion.objects.create(
            usuario=prestamo.usuario,
            prestamo=prestamo,
            mensaje=f"Has devuelto el libro '{libro.titulo}' a tiempo. ¡Gracias!"
        )
        # 🚀 Enviar correo
        asunto = "Devolución exitosa"
        mensaje = f"Gracias {prestamo.usuario.nombre}, devolviste el libro '{libro.titulo}' a tiempo. ¡Sin multas!"
        enviar_notificacion(prestamo.usuario, asunto, mensaje)
        messages.success(request, "Libro devuelto a tiempo. ¡Sin multas!")

    return redirect('listaprestamos')


@login_required
def eliminar_prestamos(request):
    if request.method == "POST":
        ids = request.POST.getlist('prestamos_ids')
        es_admin = request.user.is_superuser or es_bibliotecario(request.user)
        if es_admin:
            Prestamo.objects.filter(id__in=ids).delete()
        else:
            Prestamo.objects.filter(id__in=ids, usuario__user=request.user).delete()
    return redirect('listaprestamos')


@login_required
def listaprestamos(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    prestamos = Prestamo.objects.all().select_related('usuario', 'libro').prefetch_related('multa_set')
    usuarios = Usuario.objects.all()
    libros = Libro.objects.all()

    if request.method == 'POST':
        if 'agregar_prestamo' in request.POST and es_admin:
            libro_id = request.POST.get('libro')
            usuario_id = request.POST.get('usuario')
            fecha_limite = request.POST.get('fecha_limite')
            if libro_id and usuario_id and fecha_limite:
                usuario = Usuario.objects.get(pk=usuario_id)
                libro = Libro.objects.get(pk=libro_id)
                Prestamo.objects.create(usuario=usuario, libro=libro, fecha_limite=fecha_limite)
                messages.success(request, f"Préstamo de '{libro.titulo}' para {usuario.nombre} creado correctamente.")
            else:
                messages.error(request, "Error al crear el préstamo. Verifique los datos.")
        elif 'eliminar_seleccion' in request.POST and es_admin:
            ids = request.POST.getlist('prestamos_ids')
            if ids:
                Prestamo.objects.filter(id__in=ids).delete()
                messages.success(request, "Préstamos seleccionados eliminados correctamente.")
            else:
                messages.warning(request, "No seleccionaste ningún préstamo.")

    return render(request, 'hola/listaprestamos.html', {
        'prestamos': prestamos,
        'es_admin': es_admin,
        'usuarios': usuarios,
        'libros': libros
    })


# =========================
# RESERVAS
# =========================
@login_required
def reservas(request):
    usuario_logueado = Usuario.objects.filter(user=request.user).first()
    if not usuario_logueado:
        messages.error(request, "No se encontró un registro de usuario asociado.", extra_tags='reserva')
        return redirect('principal')

    libros_disponibles = Libro.objects.filter(ejemplares__gt=0)
    form = ReservaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        libro = form.cleaned_data['libro']
        if Reserva.objects.filter(libro=libro).exists():
            messages.error(request, f"El libro '{libro.titulo}' no está disponible ahora mismo.", extra_tags='reserva')
        else:
            reserva = form.save(commit=False)
            reserva.usuario = usuario_logueado
            reserva.save()
            messages.success(request, f"Reserva del libro '{libro.titulo}' guardada exitosamente.", extra_tags='reserva')
            return redirect('reservas')

    return render(request, 'hola/reservas.html', {
        'form': form,
        'usuarios': [usuario_logueado],
        'libros': libros_disponibles
    })


@login_required
def lista_reservas(request):
    if request.user.is_superuser or es_bibliotecario(request.user):
        reservas = Reserva.objects.all().select_related('usuario', 'libro')
    else:
        reservas = Reserva.objects.filter(usuario__user=request.user).select_related('usuario', 'libro')
    return render(request, 'hola/lista_reservas.html', {'reservas': reservas})


@login_required
def marcar_reserva_devuelto(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if reserva.estado != 'Devuelto':
        reserva.estado = 'Devuelto'
        reserva.save()
    return redirect('lista_reservas')


# =========================
# ESTADÍSTICAS Y REPORTES
# =========================
def estadisticas(request):
    top_prestados = Prestamo.objects.values("libro__titulo").annotate(total=Count("id")).order_by("-total")[:5]
    top_reservados = Reserva.objects.values("libro__titulo").annotate(total=Count("id")).order_by("-total")[:5]
    total_prestamos = Prestamo.objects.count()
    usuarios_activos = Usuario.objects.count()
    prestamos_por_dia = Prestamo.objects.annotate(dia=TruncDate("fecha_prestamo")).values("dia").annotate(total=Count("id")).order_by("dia")

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
        multa, _ = Multa.objects.get_or_create(prestamo=prestamo, defaults={'monto': 10})
        Notificacion.objects.get_or_create(
            usuario=prestamo.usuario,
            prestamo=prestamo,
            mensaje=f"Tienes una multa de ${multa.monto} por el libro '{prestamo.libro.titulo}'."
        )
    return HttpResponse("Multas y notificaciones generadas ✅")


# =========================
# PÁGINAS GENERALES
# =========================
def contacto(request):
    return render(request, "hola/contacto.html")


def redessociales(request):
    return render(request, "hola/redessociales.html")


def galerialibro(request):
    top_libros = Libro.objects.all()[:12]
    return render(request, "hola/galerialibro.html", {"top_libros": top_libros})


def escritores(request):
    top_autores = Autor.objects.all()[:12]
    return render(request, "hola/escritores.html", {"top_autores": top_autores})


def acerca(request):
    return render(request, 'hola/acercanosotros.html')


def prestamo_mensaje(request):
    mensaje = "No puedes tomar un nuevo libro, tienes multas pendientes."
    return render(request, 'hola/prestamos_mensaje.html', {'mensaje': mensaje})
