import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, date
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
                        id=int(row['id']),
                        defaults={
                            'email': row['email'],
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'role': row.get('role', 'cliente'),
                            'tipo_subscricao': row.get('tipo_subscricao') or None,
                            'foto_perfil': row.get('foto_perfil') or None,
                            'is_staff': row.get('is_staff', '').lower() == 'true',
                            'is_active': row.get('is_active', '').lower() != 'false',
                            'is_superuser': row.get('is_superuser', '').lower() == 'true',
                            'cancel_requested_at': self.parse_datetime(row.get('cancel_requested_at')),
                            'cancel_effective_from': self.parse_date(row.get('cancel_effective_from')),
                        }
                    )

                    # If user already exists, update missing fields (including foto_perfil)
                    if not created:
                        user.email = row['email']
                        user.first_name = row.get('first_name', user.first_name)
                        user.last_name = row.get('last_name', user.last_name)
                        user.role = row.get('role', user.role)
                        user.tipo_subscricao = row.get('tipo_subscricao') or user.tipo_subscricao
                        user.foto_perfil = row.get('foto_perfil') or user.foto_perfil
                        user.is_staff = row.get('is_staff', '').lower() == 'true'
                        user.is_active = row.get('is_active', '').lower() != 'false'
                        user.is_superuser = row.get('is_superuser', '').lower() == 'true'
                        user.cancel_requested_at = self.parse_datetime(row.get('cancel_requested_at'))
                        user.cancel_effective_from = self.parse_date(row.get('cancel_effective_from'))
                        user.save(update_fields=[
                            'email', 'first_name', 'last_name', 'role', 'tipo_subscricao',
                            'foto_perfil', 'is_staff', 'is_active', 'is_superuser',
                            'cancel_requested_at', 'cancel_effective_from'
                        ])

                    # Set password for newly created users
                    if created:
                        user.set_password(row.get('password', '12345'))
                        user.save()

            self.stdout.write(self.style.SUCCESS("✅ Users imported or updated"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No users.csv found."))


        # ---- CLASSES ----
        try:
            with open('core/data/classes.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    instrutor = User.objects.filter(id=row['instrutor_id']).first()
                    if instrutor:
                        Class.objects.get_or_create(
                            id=int(row['id']),
                            defaults={
                                'nome': row['nome'],
                                'instrutor': instrutor,
                                'horario_inicio': self.parse_datetime(row['horario_inicio']),
                                'duracao_min': int(row.get('duracao_min', 60)),
                                'capacidade_max': int(row.get('capacidade_max', 20)),
                            }
                        )
            self.stdout.write(self.style.SUCCESS("✅ Classes imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No classes.csv found."))

        # ---- BOOKINGS ----
        try:
            with open('core/data/bookings.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    usuario = User.objects.filter(id=row['usuario_id']).first()
                    aula = Class.objects.filter(id=row['aula_id']).first()
                    if usuario and aula:
                        Booking.objects.get_or_create(
                            id=int(row['id']),
                            defaults={
                                'usuario': usuario,
                                'aula': aula,
                                'data_reserva': self.parse_datetime(row.get('data_reserva')),
                                'status': row.get('status', '').lower() in ['true', '1', 'yes'],
                            }
                        )
            self.stdout.write(self.style.SUCCESS("✅ Bookings imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No bookings.csv found."))

        # ---- PT SESSIONS ----
        try:
            with open('core/data/pt_sessions.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aluno = User.objects.filter(id=row['aluno_id']).first()
                    instrutor = User.objects.filter(id=row['instrutor_id']).first()
                    if aluno and instrutor:
                        PTSession.objects.get_or_create(
                            id=int(row['id']),
                            defaults={
                                'aluno': aluno,
                                'instrutor': instrutor,
                                'horario': self.parse_datetime(row['horario']),
                                'duracao_min': int(row.get('duracao_min', 60)),
                                'criada_em': self.parse_datetime(row.get('criada_em')),
                            }
                        )
            self.stdout.write(self.style.SUCCESS("✅ PT Sessions imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No pt_sessions.csv found."))

        # ---- PAYMENTS ----
        try:
            with open('core/data/payments.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    usuario = User.objects.filter(id=row['usuario_id']).first()
                    if usuario:
                        Payment.objects.get_or_create(
                            id=int(row['id']),
                            defaults={
                                'usuario': usuario,
                                'mes_referencia': row['mes_referencia'],
                                'valor': Decimal(row.get('valor', '0')),
                                'data_limite': self.parse_date(row.get('data_limite')),
                                'status': row.get('status', 'por_pagar'),
                            }
                        )
            self.stdout.write(self.style.SUCCESS("✅ Payments imported"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("⚠️ No payments.csv found."))

        self.stdout.write(self.style.SUCCESS("🎉 All imports completed successfully!"))

    # --- Utility Functions ---
    def parse_datetime(self, value):
        """Safely parse timestamps"""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
        except Exception:
            return None

    def parse_date(self, value):
        """Safely parse date fields"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            try:
                return date.fromisoformat(value)
            except Exception:
                return None
