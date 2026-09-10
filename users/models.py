from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    # Quitamos el username de AbstractUser
    username = None
    email = models.EmailField(unique=True)

    # Roles
    is_client = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    # Membresía
    membership_active = models.BooleanField(default=False)
    membership_start = models.DateField(null=True, blank=True)
    membership_end = models.DateField(null=True, blank=True)

    # Configuración de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def activate_membership(self, duration_days=30):
        self.membership_active = True
        self.membership_start = timezone.now().date()
        self.membership_end = self.membership_start + \
            timezone.timedelta(days=duration_days)
        self.save()

    def deactivate_membership(self):
        self.membership_active = False
        self.membership_start = None
        self.membership_end = None
        self.save()

    def __str__(self):
        return self.email  # Ahora retornamos el email
