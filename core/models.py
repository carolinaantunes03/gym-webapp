from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('instrutor', 'Instrutor'),
    ]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    def __str__(self):
        return self.username

class Class(models.Model):
    nome = models.CharField(max_length=100)
    instrutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aulas_dadas')
    horario_inicio = models.DateTimeField()
    horario_fim = models.DateTimeField()
    capacidade = models.PositiveIntegerField()

    def __str__(self):
        return self.nome

class Booking(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    aula = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='reservas')
    data_reserva = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.aula.nome}"

class Payment(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagamentos')
    valor = models.DecimalField(max_digits=6, decimal_places=2)
    data_pagamento = models.DateField()
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} - {self.valor}€"