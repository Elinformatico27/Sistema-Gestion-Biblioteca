# hola/models.py
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.contrib.auth.models import User
from datetime import timedelta, date


# ============================
# 1. Usuario
# ============================
class Usuario(models.Model):
    TIPO_USUARIO = [
        ('lector', 'Lector'),
        ('admin', 'Administrador'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO, default='lector')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# ============================
# 2. Autor
# ============================
class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nombre


# ============================
# 3. Categoria
# ============================
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# ============================
# 4. Editorial
# ============================
class Editorial(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nombre


# ============================
# 5. Etiqueta
# ============================
class Etiqueta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# ============================
# 6. Libro
# ============================
class Libro(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('reservado', 'Reservado'),
    ]

    titulo = models.CharField(max_length=200)
    isbn = models.CharField(
        max_length=13,
        validators=[RegexValidator(regex=r'^\d{13}$', message='El ISBN debe tener 13 dígitos.')],
        unique=True
    )
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_publicacion = models.DateField()
    paginas = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    ejemplares = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='disponible')
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)


    def __str__(self):
        return f"{self.titulo} ({self.estado_real})"

    @property
    def disponible_real(self):
        prestados = Prestamo.objects.filter(libro=self, devuelto=False).count()
        return self.ejemplares - prestados

    @property
    def estado_real(self):
        return "Disponible" if self.disponible_real > 0 else "No disponible"


# ============================
# 7. Prestamo
# ============================
class Prestamo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
    devuelto = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.fecha_limite = date.today() + timedelta(days=2)
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "Devuelto" if self.devuelto else "Pendiente"
        return f"{self.usuario} → {self.libro} ({estado})"


# ============================
# 8. Reserva
# ============================
class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"{self.usuario} → {self.libro} ({self.estado})"


# ============================
# 9. Multa
# ============================
class Multa(models.Model):
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, null=True, blank=True)
    monto = models.DecimalField(max_digits=6, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    pagada = models.BooleanField(default=False)

    def __str__(self):
        estado = "Pagada" if self.pagada else "Pendiente"
        return f"Multa RD${self.monto} - ({estado})"


# ============================
# 10. Notificacion
# ============================
class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="notificaciones")
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones")
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"Notif. para {self.usuario} - {self.mensaje[:30]}..."


# ============================
# 11. Perfil
# ============================
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    def __str__(self):
        return self.user.username
