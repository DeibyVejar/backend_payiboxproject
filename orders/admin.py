from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order

# Esto hará que aparezca en el panel de Django
admin.site.register(Order)