from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    direccion_envio = models.TextField(blank=True, null=True, verbose_name="Dirección de envío")
    telefono = models.CharField(max_length=20, blank=True, null=True)
