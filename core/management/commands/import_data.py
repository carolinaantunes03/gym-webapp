import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Class, Booking, PTSession, Payment


class Command(BaseCommand):
    help = "Import data from CSV files in core/data/ into the database"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🚀 Starting data import..."))

        # ---- USERS ----
        try:
            with open('core/data/users.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user, created = User.objects.get_or_create(
                        email=row['email'],
                        defaults={
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'role': row.get('role', 'cliente'),
                            'tipo_subscricao': row.get('tipo_subscricao') or None,
                            'is_staff': row.get('is_staff', '').lower() == 'true',
                        }
                    )
                    if created:
                        user.set_password(row.get('password', '12345'))
                        user.save()
            self.stdout.write(self.style.SUCCESS("✅ Users imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No users.csv found."))

        # ---- CLASSES ----
        try:
            with open('core/data/classes.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    instrutor = User.objects.filter(email=row['instrutor_email']).first()
                    if instrutor:
                        Class.objects.get_or_create(
                            nome=row['nome'],
                            instrutor=instrutor,
                            horario_inicio=timezone.make_aware(
                                timezone.datetime.fromisoformat(row['horario_inicio'])
                            ),
                            duracao_min=int(row.get('duracao_min', 60)),
                            capacidade_max=int(row.get('capacidade_max', 20))
                        )
            self.stdout.write(self.style.SUCCESS("✅ Classes imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No classes.csv found."))

        # ---- BOOKINGS ----
        try:
            with open('core/data/bookings.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user = User.objects.filter(email=row['usuario_email']).first()
                    aula = Class.objects.filter(nome=row['aula_nome']).first()
                    if user and aula:
                        Booking.objects.get_or_create(
                            usuario=user,
                            aula=aula,
                            defaults={'status': row.get('status', 'True') == 'True'}
                        )
            self.stdout.write(self.style.SUCCESS("✅ Bookings imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No bookings.csv found."))

        # ---- PT SESSIONS ----
        try:
            with open('core/data/pt_sessions.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aluno = User.objects.filter(email=row['aluno_email']).first()
                    instrutor = User.objects.filter(email=row['instrutor_email']).first()
                    if aluno and instrutor:
                        PTSession.objects.get_or_create(
                            aluno=aluno,
                            instrutor=instrutor,
                            horario=timezone.make_aware(
                                timezone.datetime.fromisoformat(row['horario'])
                            ),
                            duracao_min=int(row.get('duracao_min', 60))
                        )
            self.stdout.write(self.style.SUCCESS("✅ PT Sessions imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No pt_sessions.csv found."))

        # ---- PAYMENTS ----
        try:
            with open('core/data/payments.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user = User.objects.filter(email=row['usuario_email']).first()
                    if user:
                        Payment.objects.get_or_create(
                            usuario=user,
                            mes_referencia=row['mes_referencia'],
                            defaults={
                                'valor': row.get('valor', 0),
                                'data_limite': row.get('data_limite'),
                                'status': row.get('status', 'por_pagar')
                            }
                        )
            self.stdout.write(self.style.SUCCESS("Payments imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("No payments.csv found."))

        self.stdout.write(self.style.SUCCESS("All imports completed successfully!"))
