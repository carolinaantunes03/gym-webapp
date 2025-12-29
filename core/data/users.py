import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gym_app.settings")
django.setup()

from core.models import User


def create_user(email, first_name, last_name, role, tipo_subscricao=None, senha="123456"):
    user, _ = User.objects.update_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "tipo_subscricao": tipo_subscricao if role == "cliente" else None,
        },
    )

    # password (sempre hashed)
    user.set_password(senha)

    # se quiseres que instrutores possam entrar no admin (opcional)
    user.is_staff = (role == "instrutor")

    user.save()
    return user


print("Criando/atualizando utilizadores fictícios...")

aluno1 = create_user("aluno1@teste.com", "Ana", "Silva", role="cliente", tipo_subscricao="estudante")
aluno2 = create_user("aluno2@teste.com", "João", "Costa", role="cliente", tipo_subscricao="adulto")

instrutor1 = create_user("instrutor1@teste.com", "Mike", "Johnson", role="instrutor")
instrutor2 = create_user("instrutor2@teste.com", "Jessica", "Antunes", role="instrutor")

print("Utilizadores criados/atualizados com sucesso!")

