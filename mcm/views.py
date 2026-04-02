import mercadopago
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from usuarios.forms import RegistroUserForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from catalogo.models import Producto, VarianteProducto
from django.db import transaction
from carrito.models import Carrito, ItemCarrito
from pedidos.models import Pedido, ItemPedido
from pedidos.forms import PedidoForm
from carrito.models import Carrito


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
        cantidad_seleccionada = int(request.POST.get('cantidad', 1))

        if not variante_id:
            messages.error(request, "Por favor, selecciona una talla antes de agregar.")
            return redirect('detalle_producto', pk=producto_id)

        variante = get_object_or_404(VarianteProducto, id=variante_id)
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            variante=variante
        )

        if creado:
            item.cantidad = cantidad_seleccionada
        else:
            item.cantidad += cantidad_seleccionada

        item.save()

        messages.success(request, f"¡Agregado! {cantidad_seleccionada}x {variante.producto.nombre} - Talla {variante.talla.nombre}")
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
        'total': total,
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


@login_required(login_url='login')
def realizar_pedido(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items_carrito = carrito.items.all()

    if not items_carrito.exists():
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de realizar el pedido.")
        return redirect('ver_carrito')

    total_carrito = carrito.total_precio()

    if request.method == 'POST':
        form = PedidoForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    pedido = form.save(commit=False)
                    pedido.usuario = request.user

                    metodo = pedido.metodo_pago
                    if metodo == 'contraentrega':
                        pedido.estado = 'preparando'
                    else:
                        pedido.estado = 'pendiente'

                    pedido.save()

                    for item in items_carrito:
                        if item.variante.stock < item.cantidad:
                            raise ValueError(f"Lo sentimos, no hay suficiente stock de {item.variante.producto.nombre}")

                        ItemPedido.objects.create(
                            pedido=pedido,
                            variante=item.variante,
                            cantidad=item.cantidad,
                            precio_historico=item.variante.producto.precio
                        )

                        item.variante.stock -= item.cantidad
                        item.variante.save()

                    items_carrito.delete()

                if metodo == 'contraentrega':
                    messages.success(request, "¡Tu pedido ha sido confirmado!")
                    return redirect('pedido_exitoso')

                else:
                    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

                    url_exito = request.build_absolute_uri('/pedido_exitoso/')
                    url_carrito = request.build_absolute_uri('/carrito/')

                    if "127.0.0.1" in url_exito:
                        url_exito = url_exito.replace("127.0.0.1", "localhost")
                        url_carrito = url_carrito.replace("127.0.0.1", "localhost")

                    preference_data = {
                        "items": [
                            {
                                "title": f"Pedido #{pedido.id} - MicroMania",
                                "quantity": 1,
                                "currency_id": "COP",
                                "unit_price": float(total_carrito)
                            }
                        ],
                        "back_urls": {
                            "success": "https://www.google.com/",
                            "failure": "https://www.google.com/",
                            "pending": "https://www.google.com/"
                        },
                        "auto_return": "approved",
                        "external_reference": str(pedido.id)
                    }

                    preference_response = sdk.preference().create(preference_data)
                    print("\n🚨 ERROR REAL DE MERCADO PAGO:", preference_response, "\n")
                    link_de_pago = preference_response["response"].get("sandbox_init_point")

                    if link_de_pago:
                        return redirect(link_de_pago)
                    else:
                        raise ValueError("Mercado Pago no devolvió un link válido. Revisa tus credenciales.")

            except ValueError as e:
                messages.error(request, str(e))
                return redirect('ver_carrito')

            except Exception as e:
                print(f"\n❌ ERROR PROCESANDO PEDIDO: {e}\n")
                messages.error(request, "Hubo un error al procesar tu orden. Inténtalo de nuevo.")
                return redirect('ver_carrito')

    else:
        form = PedidoForm()

    return render(request, 'pedido/realizar_pedido.html', {
        'form': form,
        'carrito': carrito,
        'total': total_carrito
    })

@login_required(login_url='login')
def pedido_exitoso(request):
    return render(request,'pedido/pedido_exitoso.html',{})