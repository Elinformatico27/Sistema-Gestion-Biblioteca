from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.dispatch import receiver
from django.utils import timezone
from django.db.models.signals import post_save
from django.http import HttpResponse
from django.urls import reverse
from datetime import date
from django.core.mail import send_mail
from .models import Perfil, Usuario, Libro, Prestamo, Reserva, Categoria, Autor, Multa, Notificacion
from .forms import (
    PerfilForm, PrestamoForm, ReservaForm, LibroForm, UsuarioForm,
    BuscarLibroForm, CustomUserCreationForm
)

User = get_user_model()

# =========================
# LOGIN / LOGOUT / REGISTRO
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

def logout_view(request):
    logout(request)
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
    return redirect('principal') if request.user.is_authenticated else redirect('login')

def es_bibliotecario(user):
    return user.is_authenticated and user.is_staff

@login_required
def principal(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    usuario, _ = Usuario.objects.get_or_create(
        user=request.user,
        defaults={'email': request.user.email, 'nombre': request.user.username, 'apellido': ''}
    )
    return render(request, 'hola/principal.html', {'usuario': usuario, 'perfil': perfil})

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
# PRÉSTAMOS
# =========================
@login_required
def prestamos(request):
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    form = PrestamoForm(request.POST or None, usuario_logueado=usuario_logueado)

    if request.method == 'POST' and form.is_valid():
        libro = form.cleaned_data['libro']
        if libro.disponible_real <= 0:
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


# =========================
# HOME / PRINCIPAL
# =========================
def home(request):
    return redirect('principal') if request.user.is_authenticated else redirect('login')
# =========================
@login_required
def es_bibliotecario(user):
    return user.is_authenticated and user.is_staff


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

def es_bibliotecario(user):
    return user.groups.filter(name='Bibliotecario').exists()


# =========================
# LIBROS
# =========================

@login_required
def libros_view(request):
    user = request.user

    es_admin = (
        user.is_superuser or 
        user.groups.filter(name="Bibliotecario").exists()
    )

    # ✅ Si envía formulario GUARDAMOS
    if request.method == "POST" and es_admin:
        form = LibroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Libro guardado correctamente ✅")
            return redirect('libros')  # 👉 Recarga la página y se ve en la lista
    else:
        form = LibroForm() if es_admin else None

    # ✅ Lista + filtros búsqueda como ya tenías ✅
    libros = Libro.objects.select_related("autor", "categoria").all()

    titulo = request.GET.get("titulo", "")
    autor = request.GET.get("autor", "")
    categoria = request.GET.get("categoria", "")

    if titulo:
        libros = libros.filter(titulo__icontains=titulo)
    if autor:
        libros = libros.filter(autor__nombre__icontains=autor)
    if categoria:
        libros = libros.filter(categoria__nombre__icontains=categoria)

    categorias = Categoria.objects.all()

    return render(request, 'hola/Libro.html', {
        'libros': libros,
        'categorias': categorias,
        'form': form,
        'es_admin': es_admin,
        'titulo': titulo,
        'autor': autor,
        'categoria': categoria,
    })


# =========================
# PRÉSTAMOS
# =========================
@login_required
def prestamos(request):
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    form = PrestamoForm(request.POST or None, usuario_logueado=usuario_logueado)

    if request.method == 'POST' and form.is_valid():
        libro = form.cleaned_data['libro']
        if libro.disponible_real <= 0:
            messages.error(request, f"El libro '{libro.titulo}' no tiene ejemplares disponibles.")
            return redirect('prestamos')

        prestamo = form.save(commit=False)
        if not es_admin:
            prestamo.usuario = usuario_logueado
        prestamo.save()
        Libro.objects.filter(id=libro.id).update(ejemplares=F('ejemplares') - 1)
        actualizar_inventario_y_estadisticas() 
        messages.success(request, f"Préstamo del libro '{libro.titulo}' guardado correctamente.")
        form = PrestamoForm(usuario_logueado=usuario_logueado)

    return render(request, 'hola/prestamos.html', {'form': form, 'es_admin': es_admin})

@login_required
def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if prestamo.devuelto:
        messages.warning(request, "Este préstamo ya fue devuelto.")
        return redirect("listaprestamos")

    prestamo.devuelto = True
    prestamo.fecha_devolucion = date.today()
    prestamo.save()
    Libro.objects.filter(id=prestamo.libro.id).update(ejemplares=F('ejemplares') + 1)
    actualizar_inventario_y_estadisticas()

    retraso = (prestamo.fecha_devolucion - prestamo.fecha_limite).days
    if retraso > 0:
        monto = retraso * 100
        Multa.objects.create(prestamo=prestamo, monto=monto)
        Notificacion.objects.create(
            usuario=prestamo.usuario,
            prestamo=prestamo,
            mensaje=f"Tienes una multa de ${monto} por devolver con {retraso} día(s) de retraso."
        )
        messages.error(request, f"Libro devuelto con retraso. Multa generada: ${monto}")
    else:
        Notificacion.objects.create(
            usuario=prestamo.usuario,
            prestamo=prestamo,
            mensaje="Has devuelto tu libro a tiempo. ¡Gracias!"
        )
        messages.success(request, "Libro devuelto correctamente y sin multa.")

    return redirect("listaprestamos")

@login_required
def listaprestamos(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    prestamos = Prestamo.objects.select_related('usuario','libro').prefetch_related('multa_set')
    return render(request, 'hola/listaprestamos.html', {'prestamos': prestamos, 'es_admin': es_admin})

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
def prestamo_mensaje(request):
    mensaje = "No puedes tomar un nuevo libro, tienes multas pendientes."
    return render(request, 'prestamo_mensaje.html', {'mensaje': mensaje})

# =========================
# RESERVAS
# =========================
@login_required
def reservas(request):
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)

    if request.method == "POST":
        form = ReservaForm(request.POST, usuario_logueado=usuario_logueado)
        if form.is_valid():
            reserva = form.save(commit=False)
            if not es_admin:
                reserva.usuario = usuario_logueado
            reserva.estado = 'activo'
            reserva.save()
            messages.success(request, f"Reserva del libro '{reserva.libro.titulo}' guardada correctamente ✅")
            return redirect('mis_reservas')
    else:
        form = ReservaForm(usuario_logueado=usuario_logueado)

    libros = [libro for libro in Libro.objects.all() if libro.disponible_real > 0]
    return render(request, "hola/reservas.html", {"form": form, "libros": libros, "es_admin": es_admin})




# =========================
# PERFIL USUARIO
# =========================
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
def listaprestamos(request):
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)
    prestamos = Prestamo.objects.select_related('usuario','libro').prefetch_related('multa_set')
    return render(request, 'hola/listaprestamos.html', {'prestamos': prestamos, 'es_admin': es_admin})

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
def prestamo_mensaje(request):
    mensaje = "No puedes tomar un nuevo libro, tienes multas pendientes."
    return render(request, 'prestamo_mensaje.html', {'mensaje': mensaje})

# =========================
# RESERVAS
# =========================
@login_required
def reservas(request):
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    es_admin = request.user.is_superuser or es_bibliotecario(request.user)

    libro_id = request.GET.get('libro_id')
    if libro_id:
        form = ReservaForm(initial={'libro': libro_id}, usuario_logueado=usuario_logueado)
    else:
        form = ReservaForm(usuario_logueado=usuario_logueado)

    if request.method == "POST":
        form = ReservaForm(request.POST, usuario_logueado=usuario_logueado)
        if form.is_valid():
            reserva = form.save(commit=False)
            if not es_admin:
                reserva.usuario = usuario_logueado
            reserva.estado = 'activo'
            reserva.save()
            messages.success(request, f"Reserva del libro '{reserva.libro.titulo}' guardada correctamente ✅")
            return redirect('mis_reservas')

    # Lista de libros disponibles
    libros = [libro for libro in Libro.objects.all() if libro.disponible_real > 0]

    # Lista de usuarios para el formulario
    usuarios = Usuario.objects.all() if es_admin else [usuario_logueado]

    return render(request, "hola/reservas.html", {
        "form": form,
        "libros": libros,
        "usuarios": usuarios,  # ⚡ Aseguramos que se envíe al template
        "es_admin": es_admin
    })



@login_required
def mis_reservas(request):
    usuario = get_object_or_404(Usuario, user=request.user)
    reservas = Reserva.objects.filter(usuario=usuario).select_related('libro').order_by('-fecha_inicio')
    return render(request, "hola/mis_reservas.html", {'reservas': reservas})




def estadisticas(request):
    # Total de préstamos
    total_prestamos = Prestamo.objects.count()
    
    # Total de reservas
    total_reservas = Reserva.objects.count()
    
    # Usuarios registrados
    usuarios_activos = Usuario.objects.count()
    
    # Top 5 libros prestados
    top_prestados = Prestamo.objects.values('libro__titulo')\
        .annotate(total=Count('libro'))\
        .order_by('-total')[:5]
    
    # Top 5 libros reservados
    top_reservados = Reserva.objects.values('libro__titulo')\
        .annotate(total=Count('libro'))\
        .order_by('-total')[:5]
    
    # Préstamos por día para gráfico
    prestamos_por_dia = Prestamo.objects.extra({'dia': "date(fecha_prestamo)"}).values('dia').annotate(total=Count('id')).order_by('dia')

    context = {
        'total_prestamos': total_prestamos,
        'total_reservas': total_reservas,
        'usuarios_activos': usuarios_activos,
        'top_prestados': top_prestados,
        'top_reservados': top_reservados,
        'prestamos_por_dia': prestamos_por_dia
    }
    
    return render(request, 'hola/reportesestadisticas.html', context)


@login_required
def marcar_reserva_finalizado(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.estado = 'finalizado'
    reserva.save()
    return redirect('lista_reservas')

@login_required
def limpiar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.delete()
    messages.success(request, "Reserva eliminada correctamente.")
    return redirect('lista_reservas')

@login_required
def limpiar_todas_reservas(request):
    Reserva.objects.all().delete()
    messages.success(request, "Todas las reservas se han eliminado correctamente.")
    return redirect('lista_reservas')

@login_required
def limpiar_reservas_finalizadas(request):
    finalizadas = Reserva.objects.filter(estado='finalizado')
    count = finalizadas.count()
    finalizadas.delete()
    messages.success(request, f"{count} reservas finalizadas fueron eliminadas correctamente.")
    return redirect('reservas')

@login_required
def lista_reservas(request):
    if request.user.is_superuser or es_bibliotecario(request.user):
        reservas = Reserva.objects.select_related('usuario', 'libro').order_by('-fecha_inicio')
        return render(request, 'hola/lista_reservas.html', {'reservas': reservas})
    messages.error(request, "No tienes permiso para ver esta página.")
    return redirect('principal')

# =========================
# PERFIL USUARIO
# =========================
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
    usuario = request.user
    perfil = getattr(usuario, 'perfil', None)

    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect("perfil")  # redirige a la vista de perfil
    else:
        form = PerfilForm(instance=perfil)

    # Este render asegura que siempre devuelves un HttpResponse
    return render(request, "hola/editar_perfil.html", {"form": form})


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
        # Prestamos activos (no devueltos)
        prestados = Prestamo.objects.filter(libro=libro, devuelto=False).count()
        # Reservas activas/pendientes
        reservados = Reserva.objects.filter(libro=libro, estado__in=['activo', 'pendiente']).count()
        # Disponibles reales
        disponible = max(libro.ejemplares - prestados - reservados, 0)

        inventario.append({
            'id': libro.id,
            'titulo': libro.titulo,
            'ejemplares': libro.ejemplares,
            'prestados_real': prestados,
            'reservados_real': reservados,
            'disponible_real': disponible,
        })

    # Estadísticas básicas (opcional)
    total_prestamos = Prestamo.objects.count()
    total_reservas = Reserva.objects.count()

    return render(request, 'hola/inventario_sgb.html', {
        'inventario': inventario,
        'total_prestamos': total_prestamos,
        'total_reservas': total_reservas,
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

def contacto(request):
    return render(request, 'hola/contacto.html')  # o la plantilla que uses



def galerialibro(request):
    libros = list(Libro.objects.all())

    # Asignar la imagen a cada libro manualmente
    imagenes = [
        "CasaDeEspiritus.png",
        "CienAñosSoledad.png",
        "DonQuijote.png",
        "PoesiaCompleta.png",
        "TierraDeAlborada.png",
        "LaciudadYLosperros.png",
        "Elprincipito.png",
        "LaberintoSoledad.png",
        "CuentosDeLaselva.png",
        "ElReinoDelReves.png",
        "LaInvencionDelMorel.png",
        "LaMaňosa.png"
    ]

    # Agregar la propiedad imagen_nombre a cada libro
    for i, libro in enumerate(libros):
        libro.imagen_nombre = imagenes[i] if i < len(imagenes) else "default.png"

    return render(request, "hola/galerialibro.html", {"libros": libros})



def escritores(request):
    escritores = [
        {'nombre': 'Gabriel García Márquez', 'slug': 'gabriel-garcia-marquez', 'imagen': 'hola/js/gabrielgarciamarquez.jpg'},
        {'nombre': 'Isabel Allende', 'slug': 'isabel-allende', 'imagen': 'hola/js/IsabelAllende.png'},
        {'nombre': 'Miguel de Cervantes', 'slug': 'miguel-cervantes', 'imagen': 'hola/js/MiguelCervante.png'},
        {'nombre': 'María Elena Walsh', 'slug': 'maria-elena-walsh', 'imagen': 'hola/js/MariaElenWalsh.png'},
        {'nombre': 'Juan Bosch', 'slug': 'juan-bosch', 'imagen': 'hola/js/JuanBosh.png'},
        {'nombre': 'Mario Vargas Llosa', 'slug': 'mario-vargas-llosa', 'imagen': 'hola/js/MarioVargaLLosa.png'},
        {'nombre': 'Pedro Mir', 'slug': 'pedro-mir', 'imagen': 'hola/js/PedroMir.png'},
        {'nombre': 'Octavio Paz', 'slug': 'octavio-paz', 'imagen': 'hola/js/OctavioPaz.png'},
        {'nombre': 'Pablo Neruda', 'slug': 'pablo-neruda', 'imagen': 'hola/js/PabloNeruda.png'},
        {'nombre': 'Antoine de Saint-Exupéry', 'slug': 'antoine-de-saint-exupery', 'imagen': 'hola/js/AntonioDeSaint.png'},
        {'nombre': 'Horacio Quiroga', 'slug': 'horacio-quiroga', 'imagen': 'hola/js/HoracioQuiroga.png'},
        {'nombre': 'Adolfo Bioy Casares', 'slug': 'adolfo-bioy-casares', 'imagen': 'hola/js/AdolfoBIOYCas.png'},
    ]
    return render(request, 'hola/escritores.html', {'escritores': escritores})


def detalle_escritor(request, slug):
  
    escritores_detalle = {
        'gabriel-garcia-marquez': {
            'nombre': 'Gabriel García Márquez',
            'imagen': 'hola/js/gabrielgarciamarquez.jpg',
            'biografia': 'Escritor colombiano, premio Nobel de Literatura en 1982, conocido por su obra maestra "Cien Años de Soledad".',
            'libros': [
                {'titulo': 'Cien Años de Soledad', 'url': 'https://www.google.com/search?q=Cien+Años+de+Soledad'},
                {'titulo': 'El Otoño del Patriarca', 'url': 'https://www.google.com/search?q=El+Otoño+del+Patriarca'},
                {'titulo': 'Crónica de una Muerte Anunciada', 'url': 'https://www.google.com/search?q=Crónica+de+una+Muerte+Anunciada'},
                {'titulo': 'El General en su Labio de Hierro', 'url': 'https://www.google.com/search?q=El+General+en+su+Labio+de+Hierro'},
                {'titulo': 'Del Amor y Otros Demonios', 'url': 'https://www.google.com/search?q=Del+Amor+y+Otros+Demonios'}
            ]
        },
        
        
        'isabel-allende': {
            'nombre': 'Isabel Allende',
            'imagen': 'hola/js/IsabelAllende.png',
            'biografia': 'Escritora chilena conocida por novelas como "La Casa de los Espíritus", con gran influencia del realismo mágico.',
            'libros': [
                {'titulo': 'La Casa de los Espíritus', 'url': 'https://www.google.com/search?q=La+Casa+de+los+Espíritus'},
                {'titulo': 'Eva Luna', 'url': 'https://www.google.com/search?q=Eva+Luna'},
                {'titulo': 'Paula', 'url': 'https://www.google.com/search?q=Paula+Isabel+Allende'},
                {'titulo': 'Hija de la Fortuna', 'url': 'https://www.google.com/search?q=Hija+de+la+Fortuna'},
                {'titulo': 'El Plan Infinito', 'url': 'https://www.google.com/search?q=El+Plan+Infinito'}
            ]
        },
        # ... Agrega los demás escritores aquí ...
        'pablo-neruda': {
            'nombre': 'Pablo Neruda',
            'imagen': 'hola/js/PabloNeruda.png',
            'biografia': 'Poeta chileno, premio Nobel de Literatura 1971, conocido por su poesía romántica y social.',
            'libros': [
                {'titulo': 'Veinte Poemas de Amor y una Canción Desesperada', 'url': 'https://www.google.com/search?q=Veinte+Poemas+de+Amor+y+una+Canción+Desesperada'},
                {'titulo': 'Canto General', 'url': 'https://www.google.com/search?q=Canto+General'},
                {'titulo': 'Residencia en la Tierra', 'url': 'https://www.google.com/search?q=Residencia+en+la+Tierra'},
                {'titulo': 'Odisea de una Soledad', 'url': 'https://www.google.com/search?q=Odisea+de+una+Soledad'},
                {'titulo': 'Confieso que he Vivido', 'url': 'https://www.google.com/search?q=Confieso+que+he+Vivido'}
            ]
        },
        'maria-elena-walsh': {
    'nombre': 'María Elena Walsh',
    'imagen': 'hola/js/MariaElenWalsh.png',
    'biografia': 'Escritora y poeta argentina, famosa por su literatura infantil y compromiso social.',
    'libros': [
        {'titulo': 'Manuelita', 'url': 'https://www.google.com/search?q=Manuelita'},
        {'titulo': 'El Reino del Revés', 'url': 'https://www.google.com/search?q=El+Reino+del+Revés'},
        {'titulo': 'Dailan Kifki', 'url': 'https://www.google.com/search?q=Dailan+Kifki'},
        {'titulo': 'Canciones para mirar', 'url': 'https://www.google.com/search?q=Canciones+para+mirar'},
        {'titulo': 'Versos rimados', 'url': 'https://www.google.com/search?q=Versos+rimados'}
    ]
},
'juan-bosch': {
    'nombre': 'Juan Bosch',
    'imagen': 'hola/js/JuanBosh.png',
    'biografia': 'Escritor y político dominicano, fundador del Partido Revolucionario Dominicano y prolífico cuentista.',
    'libros': [
        {'titulo': 'Cuentos escritos en el exilio', 'url': 'https://www.google.com/search?q=Cuentos+escritos+en+el+exilio'},
        {'titulo': 'La Mañosa', 'url': 'https://www.google.com/search?q=La+Mañosa'},
        {'titulo': 'Camino Real', 'url': 'https://www.google.com/search?q=Camino+Real'},
        {'titulo': 'La manigua', 'url': 'https://www.google.com/search?q=La+manigua'},
        {'titulo': 'Vino con lluvia', 'url': 'https://www.google.com/search?q=Vino+con+lluvia'}
    ]
},
'mario-vargas-llosa': {
    'nombre': 'Mario Vargas Llosa',
    'imagen': 'hola/js/MarioVargaLLosa.png',
    'biografia': 'Escritor peruano, premio Nobel de Literatura 2010, conocido por novelas políticas y sociales.',
    'libros': [
        {'titulo': 'La Ciudad y los Perros', 'url': 'https://www.google.com/search?q=La+Ciudad+y+los+Perros'},
        {'titulo': 'Conversación en La Catedral', 'url': 'https://www.google.com/search?q=Conversación+en+La+Catedral'},
        {'titulo': 'Pantaleón y las Visitadoras', 'url': 'https://www.google.com/search?q=Pantaleón+y+las+Visitadoras'},
        {'titulo': 'La Fiesta del Chivo', 'url': 'https://www.google.com/search?q=La+Fiesta+del+Chivo'},
        {'titulo': 'El Sueño del Celta', 'url': 'https://www.google.com/search?q=El+Sueño+del+Celta'}
    ]
},
'pedro-mir': {
    'nombre': 'Pedro Mir',
    'imagen': 'hola/js/PedroMir.png',
    'biografia': 'Poeta dominicano, conocido por su obra social y compromiso con la realidad de su país.',
    'libros': [
        {'titulo': 'Hay un país en el mundo', 'url': 'https://www.google.com/search?q=Hay+un+país+en+el+mundo'},
        {'titulo': 'Contracanto a Walt Whitman', 'url': 'https://www.google.com/search?q=Contracanto+a+Walt+Whitman'},
        {'titulo': 'Prosa completa', 'url': 'https://www.google.com/search?q=Prosa+completa+Pedro+Mir'},
        {'titulo': 'Obras completas', 'url': 'https://www.google.com/search?q=Obras+completas+Pedro+Mir'},
        {'titulo': 'Poemas', 'url': 'https://www.google.com/search?q=Poemas+Pedro+Mir'}
    ]
},
'octavio-paz': {
    'nombre': 'Octavio Paz',
    'imagen': 'hola/js/OctavioPaz.png',
    'biografia': 'Poeta y ensayista mexicano, premio Nobel de Literatura 1990, conocido por su obra lírica y crítica.',
    'libros': [
        {'titulo': 'El Laberinto de la Soledad', 'url': 'https://www.google.com/search?q=El+Laberinto+de+la+Soledad'},
        {'titulo': 'Piedra de Sol', 'url': 'https://www.google.com/search?q=Piedra+de+Sol'},
        {'titulo': 'Libertad bajo palabra', 'url': 'https://www.google.com/search?q=Libertad+bajo+palabra'},
        {'titulo': 'Sor Juana Inés de la Cruz', 'url': 'https://www.google.com/search?q=Sor+Juana+Inés+de+la+Cruz'},
        {'titulo': 'La Otra Voz', 'url': 'https://www.google.com/search?q=La+Otra+Voz'}
    ]
},
'pablo-neruda': {
    'nombre': 'Pablo Neruda',
    'imagen': 'hola/js/PabloNeruda.png',
    'biografia': 'Poeta chileno, premio Nobel de Literatura 1971, conocido por su poesía romántica y social.',
    'libros': [
        {'titulo': 'Veinte Poemas de Amor y una Canción Desesperada', 'url': 'https://www.google.com/search?q=Veinte+Poemas+de+Amor+y+una+Canción+Desesperada'},
        {'titulo': 'Canto General', 'url': 'https://www.google.com/search?q=Canto+General'},
        {'titulo': 'Residencia en la Tierra', 'url': 'https://www.google.com/search?q=Residencia+en+la+Tierra'},
        {'titulo': 'Odisea de una Soledad', 'url': 'https://www.google.com/search?q=Odisea+de+una+Soledad'},
        {'titulo': 'Confieso que he Vivido', 'url': 'https://www.google.com/search?q=Confieso+que+he+Vivido'}
    ]
},
'antoine-de-saint-exupery': {
    'nombre': 'Antoine de Saint-Exupéry',
    'imagen': 'hola/js/AntonioDeSaint.png',
    'biografia': 'Escritor y aviador francés, autor de "El Principito", conocido por su poesía y filosofía en narrativa infantil.',
    'libros': [
        {'titulo': 'El Principito', 'url': 'https://www.google.com/search?q=El+Principito'},
        {'titulo': 'Vuelo Nocturno', 'url': 'https://www.google.com/search?q=Vuelo+Nocturno'},
        {'titulo': 'Tierra de Hombres', 'url': 'https://www.google.com/search?q=Tierra+de+Hombres'},
        {'titulo': 'Carta a un rehén', 'url': 'https://www.google.com/search?q=Carta+a+un+rehén'},
        {'titulo': 'Piloto de guerra', 'url': 'https://www.google.com/search?q=Piloto+de+guerra'}
    ]
},
'horacio-quiroga': {
    'nombre': 'Horacio Quiroga',
    'imagen': 'hola/js/HoracioQuiroga.png',
    'biografia': 'Cuentista y dramaturgo uruguayo, conocido por sus cuentos cortos y relatos de la selva.',
    'libros': [
        {'titulo': 'Cuentos de la selva', 'url': 'https://www.google.com/search?q=Cuentos+de+la+selva'},
        {'titulo': 'Anaconda', 'url': 'https://www.google.com/search?q=Anaconda+Horacio+Quiroga'},
        {'titulo': 'Los desterrados', 'url': 'https://www.google.com/search?q=Los+desterrados+Horacio+Quiroga'},
        {'titulo': 'El infierno artificial', 'url': 'https://www.google.com/search?q=El+infierno+artificial+Horacio+Quiroga'},
        {'titulo': 'Cuentos de amor, de locura y de muerte', 'url': 'https://www.google.com/search?q=Cuentos+de+amor,+de+locura+y+de+muerte'}
    ]
},
'adolfo-bioy-casares': {
    'nombre': 'Adolfo Bioy Casares',
    'imagen': 'hola/js/AdolfoBIOYCas.png',
    'biografia': 'Escritor argentino, colaborador de Jorge Luis Borges, famoso por su literatura fantástica y policial.',
    'libros': [
        {'titulo': 'La invención de Morel', 'url': 'https://www.google.com/search?q=La+invención+de+Morel'},
        {'titulo': 'Diario de la guerra del cerdo', 'url': 'https://www.google.com/search?q=Diario+de+la+guerra+del+cerdo'},
        {'titulo': 'El sueño de los héroes', 'url': 'https://www.google.com/search?q=El+sueño+de+los+héroes'},
        {'titulo': 'El perjurio de la nieve', 'url': 'https://www.google.com/search?q=El+perjurio+de+la+nieve'},
        {'titulo': 'Dormir al sol', 'url': 'https://www.google.com/search?q=Dormir+al+sol'}
    ]
}

    }

    escritor = escritores_detalle.get(slug)
    if not escritor:
        return render(request, 'hola/error.html', {'mensaje': 'Escritor no encontrado'})

    # Este return siempre se ejecuta si se encuentra el escritor
    return render(request, 'hola/detalle_escritor.html', {'escritor': escritor})

            
        
        # Repite para los otros 11 escritores


def redessociales(request):
    return render(request, "hola/redessociales.html")


def acerca(request):
    return render(request, 'hola/acercanosotros.html')

def sitemap_html(request):
    return render(request, 'hola/sitemap.html')

def actualizar_inventario_y_estadisticas():
    """
    Actualiza los campos de inventario y reportes estadísticos.
    """
    libros = Libro.objects.all()
    
    for libro in libros:
        # Prestamos activos (no devueltos)
        prestamos_activos = Prestamo.objects.filter(libro=libro, devuelto=False).count()
        # Reservas activas/pendientes
        reservas_activas = Reserva.objects.filter(libro=libro, estado__in=['activo', 'pendiente']).count()
        # Total de ejemplares
        total = libro.ejemplares
        # Disponibles reales
        disponible = max(total - prestamos_activos - reservas_activas, 0)
        
        # Guardamos estos valores en atributos temporales para templates (sin guardar en DB)
        libro.prestados = prestamos_activos
        libro.reservados = reservas_activas
        libro.disponible_mostrar = disponible  # usar un nombre temporal para templates
    
    # Estadísticas básicas (opcional actualizar modelo/tabla de reportes si tienes)
    total_prestamos = Prestamo.objects.count()
    total_reservas = Reserva.objects.count()
    
    return {
        "total_prestamos": total_prestamos,
        "total_reservas": total_reservas,
    }

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




@login_required
def listar_multas_notificacion(request):
    if not request.user.is_superuser:
        return redirect('principal')

    hoy = timezone.now().date()
    multas = Multa.objects.filter(pagada=False, fecha__lt=hoy)

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        multa = multas.filter(prestamo__usuario_id=usuario_id).first()
        if multa:
            send_mail(
                'Notificación de Multa',
                f'Hola {multa.prestamo.usuario.username}, tienes una multa pendiente de ${multa.monto}.',
                'tucorreo@gmail.com',  # Cambia por tu correo
                [multa.prestamo.usuario.email],
                fail_silently=False,
            )
            messages.success(request, f'Correo enviado a {multa.prestamo.usuario.username}')
        return redirect('listar_multa_notificacion')

    return render(request, 'hola/listar_multas_notificacion.html', {'multas': multas})



@login_required
def devolver_libro(request, libro_id):
    # Traemos el libro
    libro = get_object_or_404(Libro, id=libro_id)

    # Solo si quieres restar de inventario de préstamos activos
    # Por ejemplo, si estabas usando Prestamo:
    prestamo = Prestamo.objects.filter(libro=libro, devuelto=False).first()
    if prestamo:
        prestamo.devuelto = True
        prestamo.fecha_devolucion = date.today()
        prestamo.save()

    # Aumentar ejemplares disponibles
    libro.ejemplares += 1
    libro.save()

    # Actualizar inventario y estadísticas
    actualizar_inventario_y_estadisticas()

    # Pasamos el libro al template
    return render(request, "hola/devolucion_exitosa.html", {"libro": libro})

# ================================
# FORMULARIO DE PRÉSTAMO DIRECTO
# ================================
@login_required
def formulario_prestamo(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    
    # Creamos el formulario pero prellenamos el libro seleccionado
    form = PrestamoForm(request.POST or None, usuario_logueado=usuario_logueado, initial={'libro': libro})

    if request.method == "POST" and form.is_valid():
        prestamo = form.save(commit=False)
        prestamo.usuario = usuario_logueado
        prestamo.save()

        # Actualizamos inventario
        libro.ejemplares -= 1
        libro.save()

        messages.success(request, f"Préstamo del libro '{libro.titulo}' registrado correctamente.")
        return redirect("listaprestamos")

    return render(request, "hola/prestamos.html", {
        "form": form,
        "libro": libro,
        "es_admin": request.user.is_superuser or request.user.groups.filter(name="Bibliotecario").exists()
    })




# ================================
# FORMULARIO DE RESERVA DIRECTO
# ================================
@login_required
def formulario_reserva(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    usuario_logueado = get_object_or_404(Usuario, user=request.user)
    
    # Creamos el formulario pero prellenamos el libro seleccionado
    form = ReservaForm(request.POST or None, usuario_logueado=usuario_logueado, initial={'libro': libro})

    if request.method == "POST" and form.is_valid():
        reserva = form.save(commit=False)
        reserva.usuario = usuario_logueado
        reserva.estado = 'activo'
        reserva.save()

        messages.success(request, f"Reserva del libro '{libro.titulo}' registrada correctamente.")
        return redirect("mis_reservas")

    return render(request, "hola/reservas.html", {
        "form": form,
        "libro": libro,
        "es_admin": request.user.is_superuser or request.user.groups.filter(name="Bibliotecario").exists()
    })


def prestar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    # aquí tu lógica de préstamo
    # ejemplo: marcar como prestado, registrar usuario, etc.
    return redirect('galerialibro')  # vuelve a la galería

def reservar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    # aquí tu lógica de reserva
    return redirect('galerialibro')
