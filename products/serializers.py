import re
from rest_framework import serializers
from .models import Product, Category


import re
from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
        nombre_limpio = value.strip()

        # Expresión regular que solo permite letras y espacios
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre_limpio):
            raise serializers.ValidationError("El nombre de la categoría solo puede contener letras y espacios.")

        return nombre_limpio


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    description = serializers.CharField(
        required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price',
                  'stock', 'image', 'category', 'category_id']
