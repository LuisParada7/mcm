from django.contrib import admin
from .models import Pedido, ItemPedido

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['subtotal_item']

    def subtotal_item(self, obj):
        if obj.id:
            precio_formateado = f"{int(obj.subtotal):,}".replace(",", ".")
            return f"${precio_formateado}"
        return "$0"
    subtotal_item.short_description = 'Subtotal'


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_completo', 'usuario', 'estado', 'metodo_pago', 'fecha_pedido',  'direccion', 'total_del_pedido']
    list_display_links = ['id', 'nombre_completo']
    list_filter = ['estado', 'metodo_pago', 'fecha_pedido', 'ciudad']
    search_fields = ['id', 'nombre_completo', 'usuario__username', 'usuario__email', 'telefono']
    readonly_fields = ['fecha_pedido']
    inlines = [ItemPedidoInline]
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'estado', 'fecha_pedido')
        }),
        ('Datos de Envío y Contacto', {
            'fields': ('nombre_completo', 'telefono', 'ciudad', 'direccion', 'detalles_direccion')
        }),
        ('Información de Pago', {
            'fields': ('metodo_pago', 'id_transaccion')
        }),
        ('Notas del Cliente', {
            'fields': ('notas_pedido',),
            'classes': ('collapse',)
        }),
    )

    def total_del_pedido(self, obj):
        total_formateado = f"{int(obj.precio_total_pedido):,}".replace(",", ".")
        return f"${total_formateado}"
    total_del_pedido.short_description = 'Total'