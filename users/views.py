from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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

        # Aquí está la clave: NO pasamos 'username'
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        return Response({"message": "Usuario registrado con éxito.", "id": user.id}, status=status.HTTP_201_CREATED)

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

# 3. 🔑 VISTA DE DETALLE


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
