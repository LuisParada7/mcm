from django.db import models
from django.conf import settings

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Categorías"

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, related_name='productos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    disponible = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False, verbose_name="¿Mostrar en Home?")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    @property
    def precio_pagina(self):
        return f"{int(self.precio):,}".replace(",", ".")

class Talla(models.Model):
    TIPO_CHOICES = [
        ('calzado', 'Numérico (Calzado)'),
        ('ropa', 'Letras (Indumentaria)'),
        ('unico', 'Talla Única / Accesorios'),
    ]
    nombre = models.CharField(max_length=10)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    def __str__(self):
        if self.tipo == 'unico':
            return self.nombre
        return f"{self.nombre} ({self.tipo})"

class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variantes")
    talla = models.ForeignKey(Talla, on_delete=models.PROTECT)

    stock=models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'talla')

    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla.nombre}"

    def esta_disponible(self):
        return self.stock > 0

class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)
    id_transaccion = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        estado = "Carrito" if not self.completado else "Completado"
        return f"Pedido {self.id} de {self.usuario.username} ({estado})"

    @property
    def precio_total_pedido(self):
        items = self.itempedido_set.all()
        total = sum([item.precio_total for item in items])
        return total

class ItemPedido(models.Model):
    variante = models.ForeignKey(VarianteProducto, on_delete=models.SET_NULL, null=True, related_name="items_pedido")

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    @property
    def precio_total(self):
        if self.variante and self.variante.producto:
             return self.variante.producto.precio * self.cantidad
        return 0

    def __str__(self):
        if self.variante:
            return f"{self.cantidad} x {self.variante.producto.nombre} (Talla: {self.variante.talla.nombre})"
        return f"{self.cantidad} x [Producto No Disponible]"
