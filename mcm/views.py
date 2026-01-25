from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from usuarios.forms import RegistroUserForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from catalogo.models import Producto

def index(request):
    return render(request,'index/index.html',{
    })

def home(request):

    productos = Producto.objects.all()

    busqueda = request.GET.get('q')
    categoria_filtro = request.GET.get('categoria')

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    elif categoria_filtro:
        productos = productos.filter(categoria__nombre=categoria_filtro)

    else:
        productos = productos.filter(destacado=True).order_by('-id')

        if not productos:
             productos = Producto.objects.all()[:8]

    data = {
        'productos': productos
    }
    return render(request, 'home/home.html', data)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'auth/login.html', context)


def register(request):
    if request.method == 'POST':
        form = RegistroUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = RegistroUserForm()

    context = {'form': form}
    return render(request, 'auth/register.html', context)