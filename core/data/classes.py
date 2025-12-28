import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_app.settings')
django.setup()

from core.models import Class, User

print("Criando aulas...")

today = datetime.now().date()

aulas_info = [
    {'nome': 'Yoga', 'instrutor_email': 'instrutor1@teste.com', 'dias': [0,2,4], 'hora_inicio': '09:00', 'duracao': 45, 'capacidade': 20},
    {'nome': 'Pilates', 'instrutor_email': 'instrutor2@teste.com', 'dias': [1,3,5], 'hora_inicio': '10:30', 'duracao': 45, 'capacidade': 15},
    {'nome': 'Cycling', 'instrutor_email': 'instrutor1@teste.com', 'dias': [0,2,4], 'hora_inicio': '18:00', 'duracao': 45, 'capacidade': 50},
]

for aula_info in aulas_info:
    instrutor = User.objects.get(email=aula_info['instrutor_email'])
    for i in range(7):
        dia = today + timedelta(days=i)
        if dia.weekday() in aula_info['dias']:
            hora, minuto = map(int, aula_info['hora_inicio'].split(':'))
            inicio = datetime.combine(dia, datetime.min.time()) + timedelta(hours=hora, minutes=minuto)
            Class.objects.get_or_create(
                nome=aula_info['nome'],
                instrutor=instrutor,
                horario_inicio=inicio,
                defaults={'duracao_min': aula_info['duracao'], 'capacidade_max': aula_info['capacidade']}
            )

print("Aulas criadas com sucesso!")
