from django.shortcuts import render
from django.db.models import Q
from catalogo.models import Producto

def index(request):
    return render(request,'index/index.html',{
    })

def home(request):
    productos = Producto.objects.filter(disponible=True, stock__gt=0)

    query = request.GET.get('q')

    if query:
        productos = productos.filter(nombre__icontains=query)

    context = {
        'productos': productos
    }
    return render(request, 'home/home.html', context)