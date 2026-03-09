from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'telefono', 'direccion_envio', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')

class CustomUserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = UserResource
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información de Envío y Contacto', {
            'fields': ('direccion_envio', 'telefono')
        }),
    )
    list_display = BaseUserAdmin.list_display + ('telefono',)

admin.site.register(User, CustomUserAdmin)