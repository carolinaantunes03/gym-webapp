from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Class, Booking, Payment
from decimal import Decimal

from .forms import LoginForm

def first_day_of_month(d: date) -> date:
    return d.replace(day=1)

def first_day_next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)

def month_key(d: date) -> str:
    return d.strftime("%Y-%m")

def due_date_for_month(month_start: date) -> date:
    # tens usado dia 10 como data limite
    return month_start.replace(day=10)

# ---------------------------
# Login
# ---------------------------
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirecionar conforme o tipo de utilizador
            if user.role == 'cliente':
                return redirect('aluno_dashboard')
            elif user.role == 'instrutor':
                return redirect('instrutor_dashboard')
            else:
                return redirect('admin:index')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


# ---------------------------
# Logout
# ---------------------------
def user_logout(request):
    logout(request)
    return redirect('login')


# ---------------------------
# Dashboards
# ---------------------------
@login_required
def aluno_dashboard(request):
    return render(request, 'aluno/dashboard.html')


@login_required
def instrutor_dashboard(request):
    return render(request, 'instrutor/dashboard.html')

def home(request):
    return render(request, 'home.html')


# ---------------------------
# Horário de Aulas
# ---------------------------
@login_required
def horario_aulas(request):
    # Dia selecionado (por querystring ?dia=2025-12-28)
    data_str = request.GET.get('dia')
    if data_str:
        dia = datetime.strptime(data_str, "%Y-%m-%d").date()
    else:
        dia = timezone.localdate()

    # Calcular óximos/dias anteriores
    dia_anterior = dia - timedelta(days=1)
    dia_seguinte = dia + timedelta(days=1)

    # Obter aulas do dia
    inicio = datetime.combine(dia, datetime.min.time())
    fim = datetime.combine(dia, datetime.max.time())

    if request.user.role == 'instrutor':
        aulas = Class.objects.filter(instrutor=request.user, horario_inicio__range=(inicio, fim)).order_by('horario_inicio')
        template = 'instrutor/horario.html'
    else:
        aulas = Class.objects.filter(horario_inicio__range=(inicio, fim)).order_by('horario_inicio')
        template = 'aluno/horario.html'

    # Reservas do utilizador atual
    reservas_user = Booking.objects.filter(usuario=request.user, status=True).values_list('aula_id', flat=True)

    context = {
        'aulas': aulas,
        'dia': dia,
        'dia_anterior': dia_anterior,
        'dia_seguinte': dia_seguinte,
        'reservas_user': reservas_user,
    }
    return render(request, template, context)


# ---------------------------
# Fazer ou cancelar reserva
# ---------------------------
@login_required
def toggle_reserva(request, aula_id):
    aula = get_object_or_404(Class, id=aula_id)

    # Só alunos podem reservar
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    reserva, criada = Booking.objects.get_or_create(usuario=request.user, aula=aula)

    if not criada:
        # Já existia → cancela
        reserva.status = not reserva.status
        reserva.save()
    else:
        # Nova reserva → ativa se ainda houver vagas
        if aula.capacidade_atual >= aula.capacidade_max:
            reserva.delete()  # remove se não houver vagas
        else:
            reserva.status = True
            reserva.save()

    return redirect('horario_aulas')

@login_required
def minhas_reservas(request):
    # Apenas alunos podem ver
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    # Reservas ativas do usuário
    reservas = Booking.objects.filter(usuario=request.user, status=True).select_related('aula', 'aula__instrutor').order_by('aula__horario_inicio')

    context = {
        'reservas': reservas,
    }
    return render(request, 'aluno/minhas_reservas.html', context)

@login_required
def minhas_aulas(request):
    # Apenas instrutores podem ver
    if request.user.role != 'instrutor':
        return redirect('horario_aulas')

    # Obter todas as aulas do instrutor
    aulas = Class.objects.filter(instrutor=request.user).order_by('horario_inicio')

    context = {
        'aulas': aulas,
    }
    return render(request, 'instrutor/minhas_aulas.html', context)




# ----------------------------
# Pagamentos (aluno)
# ----------------------------
VALORES_SUBSCRICAO = {
    'estudante': Decimal('30.00'),
    'adulto': Decimal('45.00'),
    'familiar': Decimal('90.00'),
    'senior': Decimal('30.00'),
}

def _mes_ref(dt: date) -> str:
    # Ordena bem (YYYY-MM)
    return f"{dt.year:04d}-{dt.month:02d}"

def _valor_mensalidade(user: User) -> Decimal:
    return VALORES_SUBSCRICAO.get(user.tipo_subscricao, Decimal('45.00'))

def _user_tem_subscricao_ativa_no_mes(user: User, mes_inicio: date) -> bool:
    """
    True se o user ainda tem subscrição ativa para esse mês.
    - Se não existir cancel_effective_from -> ativo
    - Se existir, só é ativo antes dessa data (1º dia do mês efetivo do cancelamento)
    """
    if hasattr(user, "cancel_effective_from") and user.cancel_effective_from:
        return mes_inicio < user.cancel_effective_from
    return True


@login_required
def pagamentos(request):
    # Apenas alunos podem ver
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    hoje = timezone.localdate()
    mes_atual = first_day_of_month(hoje)

    valor_mensalidade = _valor_mensalidade(request.user)
    tipo_sub = request.user.tipo_subscricao or 'sem subscrição'

    pagamento_atual = None

    # Só cria "pagamento atual" se o utilizador ainda tiver subscrição ativa nesse mês
    if _user_tem_subscricao_ativa_no_mes(request.user, mes_atual):
        pagamento_atual, _ = Payment.objects.get_or_create(
            usuario=request.user,
            mes_referencia=_mes_ref(mes_atual),
            defaults={
                'valor': valor_mensalidade,
                'data_limite': due_date_for_month(mes_atual),  # dia 10
                'status': 'por_pagar',
            }
        )

    historico = Payment.objects.filter(usuario=request.user).exclude(
        mes_referencia=_mes_ref(mes_atual)
    ).order_by('-mes_referencia')

    # Futuros = preview dos próximos 2 meses (não cria na base de dados - meramente visual)
    futuros = []
    m = first_day_next_month(mes_atual)
    for _ in range(2):
        if not _user_tem_subscricao_ativa_no_mes(request.user, m):
            break
        futuros.append({
            'mes': _mes_ref(m),
            'data_limite': due_date_for_month(m),
            'valor': valor_mensalidade,
        })
        m = first_day_next_month(m)

    cancel_effective_from = getattr(request.user, "cancel_effective_from", None)

    context = {
        'pagamento_atual': pagamento_atual,
        'historico': historico,
        'futuros': futuros,
        'valor_mensalidade': valor_mensalidade,
        'tipo_subscricao': tipo_sub,
        'cancel_effective_from': cancel_effective_from,
    }

    return render(request, 'aluno/pagamentos.html', context)


@require_POST
@login_required
def cancelar_subscricao(request):
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    if not hasattr(request.user, "cancel_effective_from"):
        messages.error(request, "O modelo User ainda não tem os campos de cancelamento (faz a migration primeiro).")
        return redirect('pagamentos')

    hoje = timezone.localdate()

    # regra do dia 15:
    # - até 15 -> efetivo no 1º dia do próximo mês
    # - depois do 15 -> efetivo no 1º dia do mês seguinte ao próximo
    if hoje.day <= 15:
        efetivo = first_day_next_month(hoje)
    else:
        efetivo = first_day_next_month(first_day_next_month(hoje))

    request.user.cancel_requested_at = timezone.now()
    request.user.cancel_effective_from = efetivo
    request.user.save(update_fields=['cancel_requested_at', 'cancel_effective_from'])

    Payment.objects.filter(
        usuario=request.user,
        mes_referencia__gte=_mes_ref(efetivo)
    ).delete()

    messages.success(request, f"Subscrição cancelada. Fica inativa a partir de {efetivo.strftime('%d/%m/%Y')}.")
    return redirect('pagamentos')


@login_required
def pagar_pagamento(request, pagamento_id):
    if request.method != 'POST':
        return redirect('pagamentos')

    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    pagamento = get_object_or_404(Payment, id=pagamento_id, usuario=request.user)

    if pagamento.status != 'pago':
        pagamento.status = 'pago'
        pagamento.save(update_fields=['status'])
        messages.success(request, "Pagamento marcado como pago ✅")

    return redirect('pagamentos')