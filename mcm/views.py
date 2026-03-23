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
    # 1. Traemos el carrito del usuario
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items_carrito = carrito.items.all()

    # Si el carrito está vacío, lo devolvemos para que no compre "aire"
    if not items_carrito.exists():
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de realizar el pedido.")
        return redirect('ver_carrito') # Asegúrate de que así se llame la URL de tu carrito

    total_carrito = carrito.total_precio()

    # 2. Procesamos el formulario si el usuario le dio a "Confirmar"
    if request.method == 'POST':
        form = PedidoForm(request.POST)

        if form.is_valid():
            try:
                # transaction.atomic() protege la base de datos de errores a medias
                with transaction.atomic():
                    # --- A. CREAR EL PEDIDO ---
                    pedido = form.save(commit=False)
                    pedido.usuario = request.user

                    # Definir estado inicial según el método
                    metodo = pedido.metodo_pago
                    if metodo == 'contraentrega':
                        pedido.estado = 'preparando'
                    else:
                        pedido.estado = 'pendiente'

                    pedido.save() # Guardamos para generar el ID del pedido

                    # --- B. TRASLADAR PRODUCTOS Y RESTAR STOCK ---
                    for item in items_carrito:
                        # (Opcional) Validar si alguien más compró el último mientras él llenaba el formulario
                        if item.variante.stock < item.cantidad:
                            raise ValueError(f"Lo sentimos, no hay suficiente stock de {item.variante.producto.nombre}")

                        # Creamos el renglón de la factura
                        ItemPedido.objects.create(
                            pedido=pedido,
                            variante=item.variante,
                            cantidad=item.cantidad,
                            precio_historico = item.variante.producto.precio # Asegúrate de usar el campo de precio correcto
                        )

                        # ¡Restamos el inventario!
                        item.variante.stock -= item.cantidad
                        item.variante.save()

                    # --- C. VACIAR EL CARRITO ---
                    items_carrito.delete()

                # --- D. REDIRECCIÓN SEGÚN MÉTODO DE PAGO ---
                if metodo == 'contraentrega':
                    messages.success(request, "¡Tu pedido ha sido confirmado!")
                    return redirect('pedido_exitoso') # Pásale el ID a tu vista de éxito

                else:
                    # Si es debito, credito o pse -> Lo mandamos a Mercado Pago
                    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

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
                            # Cambia estas URLs por las de tu servidor local o dominio real
                            "success": f"http://127.0.0.1:8000/pedido_exitoso/",
                            "failure": "http://127.0.0.1:8000/carrito/",
                            "pending": "http://127.0.0.1:8000/carrito/"
                        },
                        "auto_return": "approved",
                        "external_reference": str(pedido.id) # Esto nos servirá mucho después
                    }

                    preference_response = sdk.preference().create(preference_data)
                    link_de_pago = preference_response["response"].get("sandbox_init_point")

                    return redirect(link_de_pago)

            except ValueError as e:
                # Si falta stock, atrapamos el error aquí
                messages.error(request, str(e))
                return redirect('ver_carrito')
            except Exception as e:
                # Si falla Mercado Pago u otra cosa
                print(f"Error procesando pedido: {e}")
                messages.error(request, "Hubo un error al procesar tu orden. Inténtalo de nuevo.")
                return redirect('ver_carrito')

    else:
        # Si recién entra a la página (GET), mostramos el formulario vacío
        form = PedidoForm()

    return render(request, 'pedido/realizar_pedido.html', {
        'form': form,
        'carrito': carrito,
        'total': total_carrito
    })


@login_required(login_url='login')
def pedido_exitoso(request):
    return render(request,'pedido/pedido_exitoso.html',{})