import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_app.settings')
django.setup()

from core.models import Booking, Class, User

print("Criando reservas...")

aluno1 = User.objects.get(email='aluno1@teste.com')
aluno2 = User.objects.get(email='aluno2@teste.com')

# Aluno1 reserva Yoga e Cycling
for aula in Class.objects.filter(nome__in=['Yoga', 'Cycling']):
    Booking.objects.get_or_create(usuario=aluno1, aula=aula, defaults={'status': True})

# Aluno2 reserva Pilates
for aula in Class.objects.filter(nome='Pilates'):
    Booking.objects.get_or_create(usuario=aluno2, aula=aula, defaults={'status': True})

print("Reservas criadas com sucesso!")
