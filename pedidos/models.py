from django.db import models
from django.conf import settings
from catalogo.models import VarianteProducto

class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente de Pago'),
        ('preparando', 'Preparando Pedido'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )

    METODOS_PAGO = (
        ('contraentrega', 'Pago a Contraentrega'),
        ('debito', 'Tarjeta de débito'),
        ('credito', 'Tarjeta de crédito'),
        ('pse', 'PSE'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    nombre_completo = models.CharField(max_length=150, help_text="Nombre de quien recibe")
    telefono = models.CharField(max_length=20, help_text="Celular para la transportadora")
    ciudad = models.CharField(max_length=100, default='Bogotá DC')
    direccion = models.CharField(max_length=250, help_text="Dirección principal")
    detalles_direccion = models.CharField(max_length=250, blank=True, null=True, help_text="Apto, Torre, Barrio, Conjunto")
    notas_pedido = models.TextField(blank=True, null=True, help_text="Ej: Dejar en portería, timbre dañado")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    id_transaccion = models.CharField(max_length=100, null=True, blank=True, help_text="ID de Mercado Pago si aplica")

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre_completo} ({self.get_estado_display()})"

    @property
    def precio_total_pedido(self):
        return sum([item.subtotal for item in self.items.all()])


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    variante = models.ForeignKey(VarianteProducto, on_delete=models.SET_NULL, null=True)
    cantidad = models.IntegerField(default=1)
    precio_historico = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.precio_historico * self.cantidad

    def __str__(self):
        nombre_producto = self.variante.producto.nombre if self.variante else "Producto Eliminado"
        return f"{self.cantidad}x {nombre_producto} (Pedido #{self.pedido.id})"
