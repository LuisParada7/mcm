from django.db import models
from catalogo.models import Producto, VarianteProducto
from django.conf import settings

class Carrito (models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito'
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    def total_items(self):
        return sum(item.cantidad for item in self.items.all())

    def total_precio(self):
        return sum(item.subtotal() for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE,
    related_name='items')
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('carrito', 'variante')

    def __str__(self):
        return f"{self.variante.producto.nombre} ({self.variante.talla.nombre}) x {self.cantidad}"

    def subtotal(self):
        return self.variante.producto.precio * self.cantidad



