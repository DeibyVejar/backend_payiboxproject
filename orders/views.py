from rest_framework import viewsets, status
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