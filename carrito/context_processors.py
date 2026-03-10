from carrito.models import Carrito

def cantidad_carrito(request):
    total = 0
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        total = carrito.total_items()

    return {'cantidad_items_carrito': total}