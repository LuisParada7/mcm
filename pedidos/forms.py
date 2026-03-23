from django import forms
from .models import Pedido

class PedidoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 'contraentrega' es la clave que usaste en tu modelo para esa opción
        self.fields['metodo_pago'].initial = 'contraentrega'
        self.fields['metodo_pago'].choices = Pedido.METODOS_PAGO

    class Meta:
        model = Pedido
        # Solo le pedimos al usuario los datos que realmente necesitamos que llene
        fields = [
            'nombre_completo',
            'telefono',
            'ciudad',
            'direccion',
            'detalles_direccion',
            'notas_pedido',
            'metodo_pago'
        ]

        widgets = {
            'detalles_direccion': forms.TextInput(attrs={
                'placeholder': 'Ej. Apto 401, Torre 2 (Opcional)'
            }),
            'notas_pedido': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Instrucciones para el repartidor (Ej. Dejar en portería)...'
            }),
            # Usamos RadioSelect para que salgan las opciones separadas con bolitas
            'metodo_pago': forms.RadioSelect(attrs={
                'class': 'form-check-input',
                'required': 'required'
            }),
        }

        # Cambiamos un poco los textos que aparecen arriba de cada cajita
        labels = {
            'nombre_completo': 'Nombre de quien recibe',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'detalles_direccion': 'Detalles adicionales (Apto, Conjunto, etc.)',
            'notas_pedido': 'Notas para el envío (Opcional)',
            'metodo_pago': 'Selecciona tu método de pago',
        }