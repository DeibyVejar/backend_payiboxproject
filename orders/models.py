from django.db import models
from users.models import CustomUser
from products.models import Product


class Order(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('in_review', 'En revisión'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rechazado'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Transferencia
    transfer_reference = models.CharField(
        max_length=255, null=True, blank=True)
    transfer_image = models.ImageField(
        upload_to='transfers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # CAMBIO: Ahora usamos email en lugar de username
        return f"Orden {self.id} - {self.user.email}"

    def update_total(self):
        """Calcula el total basándose en los items asociados"""
        self.total = sum(
            item.price * item.quantity for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualiza el total de la orden cada vez que se guarda un item
        self.order.update_total()
