from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta


# --------------------------
# Custom User Manager
# --------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# --------------------------
# Custom User Model
# --------------------------
class User(AbstractUser):
    username = None  # Desativamos o campo username
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('cliente', 'Cliente'),
        ('instrutor', 'Instrutor'),
    ]

    TIPO_SUBS = [
        ('estudante', 'Estudante'),
        ('adulto', 'Adulto'),
        ('familiar', 'Pack Familiar'),
        ('senior', 'Sénior'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cliente')
    tipo_subscricao = models.CharField(max_length=20, choices=TIPO_SUBS, blank=True, null=True)

    USERNAME_FIELD = 'email'           # agora o login é feito com o email
    REQUIRED_FIELDS = []               # não obrigamos username
    objects = CustomUserManager()      # usamos o novo manager

    def __str__(self):
        return f"{self.email} ({self.role})"

# --------------------------
# Aula (Class)
# --------------------------
class Class(models.Model):
    nome = models.CharField(max_length=100)
    instrutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aulas_dadas', limit_choices_to={'role': 'instrutor'})
    horario_inicio = models.DateTimeField()
    duracao_min = models.PositiveIntegerField(default=60)
    capacidade_max = models.PositiveIntegerField(default=50)
    
    def __str__(self):
        return f"{self.nome} - {self.horario_inicio.strftime('%d/%m/%Y %H:%M')}"

    @property
    def horario_fim(self):
        return self.horario_inicio + timedelta(minutes=self.duracao_min)
    
    @property
    def capacidade_atual(self):
        return self.reservas.filter(status=True).count()

    @property
    def capacidade_display(self):
        return f"{self.capacidade_atual}/{self.capacidade_max}"


# --------------------------
# Reserva
# --------------------------
class Booking(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas', limit_choices_to={'role': 'cliente'})
    aula = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='reservas')
    data_reserva = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)  # True = ativa, False = cancelada

    def __str__(self):
        return f"{self.usuario.username} - {self.aula.nome}"

    class Meta:
        unique_together = ('usuario', 'aula')  # Um utilizador não pode reservar a mesma aula duas vezes


# --------------------------
# Pagamento
# --------------------------
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('por_pagar', 'Por Pagar'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagamentos')
    mes_referencia = models.CharField(max_length=20)  
    valor = models.DecimalField(max_digits=6, decimal_places=2)
    data_limite = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='por_pagar')

    def __str__(self):
        return f"{self.usuario.username} - {self.mes_referencia} ({self.status})"
