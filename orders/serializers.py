from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    # Esto obtiene el campo 'name' del modelo Product relacionado con 'product'
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    # 1. Definimos 'user' como un campo de método personalizado
    user = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'payment_method', 'status', 'total',
                  'transfer_reference', 'transfer_image', 'items', 'created_at']
        read_only_fields = ['user', 'total', 'status', 'created_at']

    # 2. Armamos el JSON del usuario combinando Nombre y Apellido
    def get_user(self, obj):
        if obj.user:
            # Combinamos el nombre y apellido real guardados en la BD
            nombre_completo = f"{obj.user.first_name} {obj.user.last_name}".strip(
            )

            return {
                # Se lo enviamos como 'username' para que Angular lo pinte arriba automáticamente
                'username': nombre_completo if nombre_completo else "Cliente sin Nombre",
                'email': obj.user.email
            }
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['transfer_reference', 'transfer_image', 'status']
