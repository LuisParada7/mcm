from django.contrib import admin
from .models import Categoria, Producto, Pedido, ItemPedido
from import_export.admin import ImportExportModelAdmin

# Configuración para ver los items DENTRO del pedido
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('precio_total_calculado',)
    can_delete = True

    def precio_total_calculado(self, obj):
        return obj.precio_total
    precio_total_calculado.short_description = "Subtotal"


@admin.register(Categoria)
class CategoriaAdmin(ImportExportModelAdmin):
    list_display = ('nombre', 'descripcion_corta', 'cantidad_productos')
    search_fields = ('nombre',)
    ordering = ['nombre']

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if obj.descripcion and len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = "Descripción"

    def cantidad_productos(self, obj):
        return obj.productos.count()
    cantidad_productos.short_description = "Nº Productos"


@admin.register(Producto)
class ProductoAdmin(ImportExportModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'disponible', 'fecha_creacion')
    list_filter = ('categoria', 'disponible', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    ordering = ['-fecha_creacion']
    list_editable = ('precio', 'stock', 'disponible')

    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'categoria', 'descripcion')
        }),
        ('Inventario y Precios', {
            'fields': ('precio', 'stock', 'disponible')
        }),
        ('Multimedia', {
            'fields': ('imagen',)
        }),
    )


@admin.register(Pedido)
class PedidoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'completado', 'total_pagar', 'id_transaccion')
    list_filter = ('completado', 'fecha_pedido')
    search_fields = ('usuario__username', 'usuario__email', 'id_transaccion')
    ordering = ['-fecha_pedido']

    inlines = [ItemPedidoInline]

    def total_pagar(self, obj):
        return f"${obj.precio_total_pedido}"
    total_pagar.short_description = "Total del Pedido"

    fieldsets = (
        ('Datos del Cliente', {
            'fields': ('usuario', 'fecha_pedido')
        }),
        ('Estado del Pedido', {
            'fields': ('completado', 'id_transaccion')
        }),
    )

    readonly_fields = ('fecha_pedido',)


@admin.register(ItemPedido)
class ItemPedidoAdmin(ImportExportModelAdmin):

    list_display = ('pedido', 'producto', 'cantidad', 'subtotal_item')
    list_filter = ('fecha_agregado',)
    search_fields = ('pedido__usuario__username', 'producto__nombre')

    def subtotal_item(self, obj):
        return obj.precio_total
    subtotal_item.short_description = "Subtotal"
