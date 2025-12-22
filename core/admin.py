from django.contrib import admin
from .models import User, Class, Booking, Payment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'tipo')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('nome', 'instrutor', 'horario_inicio', 'horario_fim', 'capacidade')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'aula', 'data_reserva', 'status')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'valor', 'data_pagamento', 'status')
