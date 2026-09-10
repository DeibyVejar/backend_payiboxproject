from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """Serializador para mostrar info del usuario"""
    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'first_name',       # ✨ Añadido para poder leerlo en el perfil de Angular
            'last_name',        # ✨ Añadido para poder leerlo en el perfil de Angular
            'is_client',
            'is_admin',
            'membership_active',
            'membership_start',
            'membership_end',
            'created_at',
        )


class RegisterSerializer(serializers.ModelSerializer):
    """Serializador para registrar usuario"""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        # 1. Añadimos 'first_name' y 'last_name' para permitir su entrada desde Angular
        fields = ('first_name', 'last_name', 'email', 'password')

    def create(self, validated_data):
        # 2. Pasamos los nuevos campos extraídos al método create_user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
