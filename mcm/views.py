from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from usuarios.forms import RegistroUserForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from catalogo.models import Producto, VarianteProducto, Pedido, ItemPedido
from carrito.models import Carrito, ItemCarrito

def index(request):
    return render(request,'index/index.html',{})

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


def detalle_producto(request, pk):
    """Muestra los detalles de un producto específico y sus tallas disponibles"""
    producto = get_object_or_404(Producto, pk=pk)
    variantes_disponibles = producto.variantes.filter(stock__gt=0).order_by('talla__tipo', 'talla__nombre')

    context = {
        'producto': producto,
        'variantes_disponibles': variantes_disponibles
    }
    return render(request, 'home/detalle_producto.html', context)

@login_required(login_url='login')
def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        variante_id = request.POST.get('variante_id')

        if not variante_id:
            messages.error(request, "Por favor, selecciona una talla antes de agregar.")
            return redirect('detalle_producto', pk=producto_id)

        variante = get_object_or_404(VarianteProducto, id=variante_id)
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            variante=variante
        )

        if not creado:
            item.cantidad += 1
        item.save()

        messages.success(request, f"¡Agregado! {variante.producto.nombre} - Talla {variante.talla.nombre}")
        return redirect('detalle_producto', pk=producto_id)

    return redirect('detalle_producto', pk=producto_id)

@login_required(login_url='login')
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.select_related('variante__producto', 'variante__talla')

    total = carrito.total_precio()
    return render(request, 'carrito/ver_carrito.html', {
        'carrito': carrito,
        'items': items,
        'total': total
    })


@login_required(login_url='login')
def eliminar_del_carrito(request, producto_id):
    """Elimina un item del carrito basado en el ID del producto padre"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    item = carrito.items.filter(variante__producto_id=producto_id).first()

    if item:
        item.delete()
        messages.warning(request, "Producto eliminado del carrito.")

    return redirect('ver_carrito')

@login_required(login_url='login')
def limpiar_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    carrito.items.all().delete()
    messages.info(request, "Carrito vaciado.")
    return redirect('ver_carrito')