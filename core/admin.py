from django.contrib import admin
from .models import User, Class, Booking, Payment, PTSession


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'tipo_subscricao', 'is_active', 'is_staff')
    list_filter = ('role', 'tipo_subscricao')
    search_fields = ('email',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('nome', 'instrutor', 'horario_inicio', 'duracao_min', 'capacidade_display')
    list_filter = ('instrutor',)
    search_fields = ('nome',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'aula', 'data_reserva', 'status')
    list_filter = ('status',)
    # corrigido (tinhas com underscore, o correto é __)
    search_fields = ('usuario__email', 'aula__nome')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mes_referencia', 'valor', 'status', 'data_limite')
    list_filter = ('status', 'mes_referencia')


@admin.register(PTSession)
class PTSessionAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'instrutor', 'horario')
    list_filter = ('instrutor',)
    search_fields = ('aluno__email', 'instrutor__email', 'aluno__username', 'instrutor__username')
