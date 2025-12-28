
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_app.settings')
django.setup()

from core.models import Payment, User

print("Criando pagamentos...")

today = datetime.now().date()
pagamentos_meses = ['Janeiro 2025', 'Fevereiro 2025', 'Março 2025']

valores_subscricao = {
    'estudante': Decimal('30.00'),
    'adulto': Decimal('45.00'),
    'familiar': Decimal('90.00'),
    'senior': Decimal('30.00'),
}

for email in ['aluno1@teste.com', 'aluno2@teste.com']:
    aluno = User.objects.get(email=email)
    for i, mes in enumerate(pagamentos_meses):
        Payment.objects.get_or_create(
            usuario=aluno,
            mes_referencia=mes,
            defaults={
                'valor': valores_subscricao.get(aluno.tipo_subscricao, Decimal('50.00')),
                'status': 'pago' if i == 0 else 'por_pagar',
                'data_limite': today + timedelta(days=7*(i+1))
            }
        )

print("Pagamentos criados com sucesso!")
