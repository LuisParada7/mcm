from django.contrib import admin
from .models import Carrito, ItemCarrito

class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    raw_id_fields = ('variante',)
    readonly_fields = ('subtotal_item',)

    def subtotal_item(self, obj):
        return f"${obj.subtotal()}"
    subtotal_item.short_description = "Subtotal"

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'creado', 'total_items_display', 'total_precio_display', 'actualizado')
    list_filter = ('creado', 'actualizado')
    search_fields = ('usuario__username', 'usuario__email')

    inlines = [ItemCarritoInline]

    readonly_fields = ('creado', 'actualizado', 'total_items_display', 'total_precio_display')

    def total_items_display(self, obj):
        return obj.total_items()
    total_items_display.short_description = "Cant. Productos"

    def total_precio_display(self, obj):
        return f"${obj.total_precio()}"
    total_precio_display.short_description = "Total ($)"
