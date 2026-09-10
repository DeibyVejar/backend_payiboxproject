from rest_framework import serializers
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False  # <--- ESTO ES LO QUE FALTA
    )
    description = serializers.CharField(
        required=False, allow_blank=True)  # <--- AÑADE ESTO

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price',
                  'stock', 'image', 'category', 'category_id']
