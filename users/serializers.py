import re
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
            'first_name',
            'last_name',
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
        fields = ('first_name', 'last_name', 'email', 'password')

    def validate_first_name(self, value):
        nombre = value.strip()
        # Permite letras (con acentos y ñ) y espacios
        if not nombre or not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise serializers.ValidationError("El nombre solo debe contener letras.")
        return nombre

    def validate_last_name(self, value):
        apellido = value.strip()
        # Permite letras (con acentos y ñ) y espacios
        if not apellido or not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellido):
            raise serializers.ValidationError("El apellido solo debe contener letras.")
        return apellido

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user