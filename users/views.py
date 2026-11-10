from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.utils.html import strip_tags
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db.models import Sum, Count, F
from datetime import datetime
from orders.models import OrderItem, Order

User = get_user_model()

# 1. 🔑 VISTA DE REGISTRO
class RegisterView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not email or not password:
            return Response(
                {"error": "Por favor, rellena todos los campos obligatorios (email, password)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response({"error": "El correo electrónico ya está registrado."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Enviar correo de bienvenida automático en HTML
        self.enviar_correo_bienvenida(user)

        return Response({"message": "Usuario registrado con éxito.", "id": user.id}, status=status.HTTP_201_CREATED)

    def enviar_correo_bienvenida(self, user):
        cliente_email = user.email
        nombre_cliente = user.first_name or "Atleta"
        logo_url = "https://payibox-angular-omhn8tfw4-payibox.vercel.app/images/payiboxlogo2.png"
        tienda_url = "https://payibox-angular.vercel.app/store"

        asunto = "¡Bienvenido a la familia Payibox Gym! 🏋️‍♂️"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Encabezado con Logo -->
                <div style="background-color: #18181b; padding: 25px; text-align: center;">
                    <img src="{logo_url}" alt="Payibox Logo" style="max-height: 55px; margin-bottom: 8px;" onError="this.style.display='none'">
                    <h1 style="color: #ffc107; margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 1px;">PAYIBOX GYM</h1>
                </div>

                <!-- Cuerpo del mensaje -->
                <div style="padding: 30px; color: #27272a;">
                    <h2 style="margin-top: 0; color: #18181b;">¡Hola, {nombre_cliente}! 👋</h2>
                    <p style="font-size: 15px; line-height: 1.6;">
                        Nos alegra enormemente darte la bienvenida a la plataforma oficial de <strong>Payibox Gym</strong>.
                        A partir de ahora, tu cuenta se encuentra activa y lista para ser utilizada.
                    </p>

                    <div style="margin: 25px 0; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #ffc107; border-radius: 4px;">
                        <h4 style="margin: 0 0 10px 0; color: #18181b; font-size: 16px;">¿Qué puedes hacer en Payibox?</h4>
                        <ul style="margin: 0; padding-left: 20px; color: #52525b; font-size: 14px; line-height: 1.8;">
                            <li>Explorar nuestro catálogo de productos y suplementos deportivos.</li>
                            <li>Realizar pedidos de forma rápida y adjuntar tus comprobantes de pago.</li>
                            <li>Consultar tus planes e historial de compras en tiempo real.</li>
                        </ul>
                    </div>

                    <!-- Botón de Acción -->
                    <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
                        <a href="{tienda_url}" style="background-color: #ffc107; color: #18181b; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 6px; font-size: 15px; display: inline-block;">
                            Explorar la Tienda
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #71717a; margin-top: 30px;">¡Gracias por unirte a nosotros y dar lo mejor en cada entrenamiento!</p>
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
            print(f"Error al enviar correo de bienvenida a {user.email}: {e}")

# 2. 🔑 VISTA DE LISTA
class UserListAPIView(APIView):
    def get(self, request):
        usuarios = User.objects.all()
        data = [
            {
                "id": u.id,
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "email": u.email,
                "role": "admin" if u.is_staff else "client"
            }
            for u in usuarios
        ]
        return Response(data, status=status.HTTP_200_OK)

# 3. 🔑 VISTA DE DETALLE (CON SOPORTE PARA ELIMINAR)
class UserDetailView(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        usuario = self.get_object(pk)
        if not usuario:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if 'name' in data:
            partes = data['name'].split(' ', 1)
            usuario.first_name = partes[0]
            usuario.last_name = partes[1] if len(partes) > 1 else ''

        nuevo_email = data.get('email', '').strip().lower()
        if nuevo_email and nuevo_email != usuario.email.lower():
            if User.objects.filter(email__iexact=nuevo_email).exists():
                return Response({"error": "El correo ya está en uso."}, status=status.HTTP_400_BAD_REQUEST)
            usuario.email = nuevo_email

        if 'role' in data:
            usuario.is_staff = (data['role'] == 'admin')

        if data.get('password'):
            usuario.set_password(data['password'])

        usuario.save()
        return Response({
            "id": usuario.id,
            "name": f"{usuario.first_name} {usuario.last_name}".strip(),
            "email": usuario.email,
            "role": "admin" if usuario.is_staff else "client"
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        usuario = self.get_object(pk)
        if not usuario:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Evita que el administrador autenticado borre su propia cuenta
        if request.user.is_authenticated and usuario.id == request.user.id:
            return Response(
                {"error": "No puedes eliminar tu propia cuenta de administrador."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usuario.delete()
            return Response({"message": "Usuario eliminado con éxito."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"No se pudo eliminar el usuario: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

# 4. 🔑 RECUPERACIÓN DE CONTRASEÑA - SOLICITUD
class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'El correo electrónico es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = f"https://payibox-angular.vercel.app/reset-password/{uid}/{token}"

            subject = "Recuperación de contraseña - Payibox"
            message = (
                f"Hola {user.first_name or 'usuario'},\n\n"
                f"Haz clic en el siguiente enlace para restablecer tu contraseña en Payibox:\n"
                f"{reset_url}\n\n"
                f"Si no solicitaste este cambio, por favor ignora este correo."
            )

            send_mail(subject, message, 'noreply@payibox.com', [user.email], fail_silently=False)

        except User.DoesNotExist:
            pass

        return Response(
            {'message': 'Si el correo está registrado, recibirás las instrucciones para restablecer tu contraseña.'},
            status=status.HTTP_200_OK
        )

# 5. 🔑 RECUPERACIÓN DE CONTRASEÑA - CONFIRMACIÓN
class ResetPasswordConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('password')

        if not all([uidb64, token, new_password]):
            return Response({'error': 'Faltan parámetros obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Contraseña restablecida con éxito.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'El enlace es inválido o ha expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Usuario no encontrado o token corrupto.'}, status=status.HTTP_400_BAD_REQUEST)


TASA_CAMBIO_ACTUAL = 0.0095  # Ejemplo: 1 COP = 0.0095 Bs.

class TasaCambioView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "tasa_cop_ves": TASA_CAMBIO_ACTUAL
        }, status=status.HTTP_200_OK)

    def post(self, request):
        global TASA_CAMBIO_ACTUAL
        nueva_tasa = request.data.get('tasa_cop_ves')

        if not nueva_tasa:
            return Response({"error": "Debes ingresar una tasa válida."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            TASA_CAMBIO_ACTUAL = float(nueva_tasa)
            return Response({
                "message": "Tasa actualizada con éxito.",
                "tasa_cop_ves": TASA_CAMBIO_ACTUAL
            }, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "El valor debe ser numérico."}, status=status.HTTP_400_BAD_REQUEST)


class DashboardStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        hoy = timezone.now().date()
        mes_actual = timezone.now().month
        anio_actual = timezone.now().year

        # 1. Productos vendidos HOY (Filtrado estricto por la fecha de hoy)
        try:
            productos_hoy = (
                OrderItem.objects.filter(
                    order__created_at__date=hoy,
                    order__status='confirmed'
                )
                .values('product__id', 'product__name')
                .annotate(
                    total_vendido=Sum('quantity'),
                    ingresos_totales=Sum(F('quantity') * F('price'))
                )
                .order_by('-total_vendido')
            )
        except Exception as e:
            print("Error en productos_hoy:", e)
            productos_hoy = []

        # 2. Ranking Top 5 del Mes
        try:
            top_productos_mes = (
                OrderItem.objects.filter(
                    order__created_at__month=mes_actual,
                    order__created_at__year=anio_actual,
                    order__status='confirmed'
                )
                .values('product__id', 'product__name')
                .annotate(
                    total_vendido=Sum('quantity'),
                    ingresos_totales=Sum(F('quantity') * F('price'))
                )
                .order_by('-total_vendido')[:5]
            )
        except Exception as e:
            print("Error en top_productos_mes:", e)
            top_productos_mes = []

        # 3. Conteo de órdenes
        try:
            ventas_hoy_count = Order.objects.filter(created_at__date=hoy, status='confirmed').count()
            ventas_mes_count = Order.objects.filter(created_at__month=mes_actual, created_at__year=anio_actual, status='confirmed').count()
        except Exception:
            ventas_hoy_count, ventas_mes_count = 0, 0

        return Response({
            "productos_hoy": list(productos_hoy),
            "top_productos": list(top_productos_mes),
            "resumen": {
                "ventas_hoy_count": ventas_hoy_count,
                "ventas_mes_count": ventas_mes_count,
            }
        }, status=status.HTTP_200_OK)