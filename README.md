# Sistema-Gestion-Biblioteca
Sistema Gestion de Biblioteca
# Grupo #4 - Sistema de Gestión de Biblioteca

**Integrantes:**  
- Felix Roman Lebron  
- Yanelli Castillo Castro  

**Saludos al maestro:** Albert Grullón

---

## Descripción del Proyecto

Este proyecto es una **aplicación web desarrollada en Django** para la gestión integral de una biblioteca.  
Permite controlar usuarios, libros, autores, categorías, editoriales, préstamos, reservas, multas y notificaciones, todo en una interfaz sencilla y segura.

El proyecto fue desarrollado como parte del monográfico del curso, con el objetivo de implementar un sistema funcional para la administración de una biblioteca académica.

---

## Funcionalidades Principales

### 1. Usuarios
- Registro y control de lectores y administradores.  
- Control de tipo de usuario (`lector` o `admin`).  

### 2. Libros
- Registro de libros con título, ISBN, autor, categoría, editorial y número de páginas.  
- Control de estado: disponible, prestado o reservado.  
- Gestión de etiquetas para clasificar los libros.  

### 3. Autores, Categorías y Editoriales
- Gestión de información básica de autores, categorías y editoriales.  

### 4. Préstamos y Reservas
- Registro de préstamos de libros a usuarios.  
- Fecha límite automática de devolución (5 días).  
- Registro de reservas con estados: pendiente, activo o finalizado.  

### 5. Multas
- Registro de multas relacionadas a préstamos no devueltos.  
- Control de multas pagadas o pendientes.  

### 6. Notificaciones
- Permite almacenar notificaciones para los usuarios relacionadas a préstamos y reservas.  

---

## Requisitos

- **Python 3.13**  
- **Django 5.2.4**  
- **SQLite** (base de datos por defecto)  

---

## Instalación y Ejecución

1. Descargar o clonar el repositorio.  
2. Crear un entorno virtual:``
   ```bash
   python -m venv env

Activar el entorno virtual:

Windows:

env\Scripts\activate

source env/bin/activate

pip install -r requirements.txt

python manage.py migrate

  python manage.py createsuperuser

python manage.py runserver

http://127.0.0.1:8000/

  
 
