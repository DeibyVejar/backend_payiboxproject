from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    UserDetailView,
    UserListAPIView,
    RequestPasswordResetView,
    ResetPasswordConfirmView,
    TasaCambioView,
    DashboardStatsView,
)

urlpatterns = [
    path('', UserListAPIView.as_view(), name='user_list'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Rutas para recuperación de contraseña
    path('password-reset/', RequestPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),

    # Rutas de endpoints estáticos
    path('tasa-cambio/', TasaCambioView.as_view(), name='tasa_cambio'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard_stats'),

    # Detalle de usuario por ID (SIEMPRE al final absoluto para no colisionar)
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]