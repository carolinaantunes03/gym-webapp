import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_app.settings')
django.setup()

from core.models import User

# -----------------------------
# Criar usuários fictícios
# -----------------------------
def create_user(email, role, tipo_subscricao=None, senha='123456'):
    user, created = User.objects.get_or_create(email=email)
    if created:
        user.role = role
        user.tipo_subscricao = tipo_subscricao
        user.set_password(senha)
        if role == 'instrutor':
            user.is_staff = True
        user.save()
    return user

print("Criando usuários fictícios...")

aluno1 = create_user('aluno1@teste.com', role='cliente', tipo_subscricao='estudante')
aluno2 = create_user('aluno2@teste.com', role='cliente', tipo_subscricao='adulto')
instrutor1 = create_user('instrutor1@teste.com', role='instrutor')
instrutor2 = create_user('instrutor2@teste.com', role='instrutor')

print("Usuários criados com sucesso!")