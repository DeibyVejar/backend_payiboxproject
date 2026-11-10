from django.db import transaction
from django.core.mail import send_mail
from django.utils.html import strip_tags
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer, OrderUpdateSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()

        if user.is_staff or getattr(user, 'is_admin', False):
            return Order.objects.all().order_by('-created_at').distinct()

        return Order.objects.filter(user=user).order_by('-created_at').distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderSerializer

    def update(self, request, *args, **kwargs):
        user = request.user
        if 'status' in request.data and not (user.is_staff or getattr(user, 'is_admin', False)):
            return Response(
                {"error": "No tienes permisos de administrador para cambiar el estado de este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        user = request.user
        if 'status' in request.data and not (user.is_staff or getattr(user, 'is_admin', False)):
            return Response(
                {"error": "No tienes permisos de administrador para cambiar el estado de este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        orden_previa = self.get_object()
        estado_anterior = orden_previa.status

        orden_actualizada = serializer.save()
        nuevo_estado = orden_actualizada.status

        # Lógica de inventario: Descuento solo cuando pasa a 'confirmed'
        if estado_anterior != 'confirmed' and nuevo_estado == 'confirmed':
            with transaction.atomic():
                for item in orden_actualizada.items.all():
                    if item.product.stock < item.quantity:
                        raise serializers.ValidationError(
                            f"Stock insuficiente para '{item.product.name}'. "
                            f"Disponible: {item.product.stock}, Solicitado: {item.quantity}"
                        )

                for item in orden_actualizada.items.all():
                    producto = item.product
                    producto.stock -= item.quantity
                    producto.save()

        # Notificación por correo con logo HTML
        if estado_anterior != nuevo_estado:
            self.enviar_correo_notificacion(orden_actualizada, nuevo_estado)

    def enviar_correo_notificacion(self, orden, nuevo_estado):
        cliente_email = orden.user.email
        nombre_cliente = orden.user.first_name or "Cliente"
        logo_url = "https://payibox-angular-omhn8tfw4-payibox.vercel.app/images/payiboxlogo2.png" # URL de tu logo en Vercel

        if nuevo_estado == 'confirmed':
            asunto = f"¡Compra Confirmada! - Orden #{orden.id} | Payibox"
            badge_color = "#28a745"
            badge_text = "CONFIRMADA"
            mensaje_cuerpo = (
                f"¡Buenas noticias! Tu pago para la <strong>Orden #{orden.id}</strong> ha sido verificado y confirmado con éxito.<br><br>"
                f"<strong>Monto total:</strong> ${orden.total} COP<br><br>"
                f"Ya estamos preparando tu pedido. Puedes consultar el detalle completo desde tu perfil en nuestra plataforma."
            )
        elif nuevo_estado == 'rejected':
            asunto = f"Actualización sobre tu Orden #{orden.id} | Payibox"
            badge_color = "#dc3545"
            badge_text = "RECHAZADA"
            mensaje_cuerpo = (
                f"Lamentamos informarte que no hemos podido verificar el pago adjunto para la <strong>Orden #{orden.id}</strong>.<br><br>"
                f"Si consideras que se trata de un error o deseas adjuntar un nuevo comprobante, por favor ponte en contacto con nuestro equipo de atención."
            )
        else:
            return

        # Estructura HTML estilizada del correo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Encabezado con Logo -->
                <div style="background-color: #18181b; padding: 20px; text-align: center;">
                    <img src="{logo_url}" alt="Payibox Logo" style="max-height: 50px; margin-bottom: 8px;" onError="this.style.display='none'">
                    <h1 style="color: #ffc107; margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 1px;">PAYIBOX GYM</h1>
                </div>

                <!-- Cuerpo del mensaje -->
                <div style="padding: 30px; color: #27272a;">
                    <h2 style="margin-top: 0; color: #18181b;">Hola, {nombre_cliente}</h2>
                    <p style="font-size: 15px; line-height: 1.6;">{mensaje_cuerpo}</p>

                    <div style="margin: 25px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid {badge_color}; border-radius: 4px;">
                        <span style="font-size: 13px; text-transform: uppercase; color: #71717a; font-weight: bold;">Estado del Pedido</span>
                        <h3 style="margin: 5px 0 0 0; color: {badge_color}; font-size: 18px;">{badge_text}</h3>
                    </div>

                    <p style="font-size: 14px; color: #71717a; margin-top: 30px;">¡Gracias por entrenar y confiar en Payibox!</p>
                </div>

                <!-- Pie de página -->
                <div style="background-color: #f4f4f5; padding: 15px; text-align: center; font-size: 12px; color: #a1a1aa;">
                    © Payibox Gym. Todos los derechos reservados.
                </div>
            </div>
        </body>
        </html>
        """

        text_content = strip_tags(html_content)

        try:
            send_mail(
                subject=asunto,
                message=text_content,
                from_email='noreply@payibox.com',
                recipient_list=[cliente_email],
                html_message=html_content,
                fail_silently=True
            )
        except Exception as e:
            print(f"Error enviando correo de la orden #{orden.id}: {e}")