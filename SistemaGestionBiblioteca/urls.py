from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from hola import views

# Redirige la raíz al login
def root_redirect(request):
    return redirect('/login/')

urlpatterns = [
    path('', root_redirect),  # raíz va al login
    path('admin/', admin.site.urls),
    path('', include('hola.urls')),  # tu app principal
    path('sitemap/', views.sitemap_html, name='sitemap_html'),  # opcional
]
