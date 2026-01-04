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
from collections import Counter
from django.db.models import Count, Sum  # <-- acrescentei Sum

from .forms import ClienteSignupForm, InstrutorSignupForm
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from .models import PTSession, User, Class

from django.urls import reverse

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

def prev_month_start(d: date) -> date:
    d = d.replace(day=1)
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)


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
    return redirect('home')


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
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from core.models import Class

@login_required
def horario_aulas(request):
    # Segunda-feira da semana atual
    hoje = timezone.localdate()
    offset = int(request.GET.get("offset", 0))
    inicio_semana = hoje - timedelta(days=hoje.weekday()) + timedelta(weeks=offset)
    fim_semana = inicio_semana + timedelta(days=6)

    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]
    horas = list(range(7, 21))  # 7h–20h

    aulas = (
        Class.objects.filter(
            horario_inicio__gte=timezone.make_aware(
                timezone.datetime.combine(inicio_semana, timezone.datetime.min.time())
            ),
            horario_inicio__lt=timezone.make_aware(
                timezone.datetime.combine(fim_semana + timedelta(days=1), timezone.datetime.min.time())
            ),
        )
        .select_related("instrutor")
        .order_by("horario_inicio")
    )

    # Dicionário de horários
    horarios = {dia: {hora: [] for hora in horas} for dia in dias_semana}
    for aula in aulas:
        dt_local = aula.horario_inicio.astimezone(timezone.get_current_timezone())
        dia = dt_local.date()
        hora = dt_local.hour
        if dia in horarios and hora in horarios[dia]:
            horarios[dia][hora].append(aula)

    context = {
        "dias_semana": dias_semana,
        "horas": horas,
        "horarios": horarios,
        "semana_anterior": offset - 1,
        "semana_seguinte": offset + 1,
    }

    if request.user.role == "cliente":
        # IDs das aulas já reservadas pelo aluno
        minhas_reservas_ids = set(
            Booking.objects.filter(usuario=request.user, status=True).values_list('aula_id', flat=True)
        )
        context["minhas_reservas_ids"] = minhas_reservas_ids
        template = "aluno/horario.html"
    else:
        # instrutor
        template = "instrutor/horario.html"

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
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    agora = timezone.now()

    reservas_aulas = list(
        Booking.objects.filter(usuario=request.user, status=True, aula__horario_inicio__gte=agora)
        .select_related('aula', 'aula__instrutor')
        .order_by('aula__horario_inicio')
    )

    reservas_pt = list(
        PTSession.objects.filter(aluno=request.user, horario__gte=agora)
        .select_related('instrutor')
        .order_by('horario')
    )

    eventos = []
    for r in reservas_aulas:
        eventos.append({
            'tipo': 'aula',
            'data': r.aula.horario_inicio,
            'nome': r.aula.nome,
            'duracao': r.aula.duracao_min,
            'instrutor': r.aula.instrutor.display_name,
            'capacidade': r.aula.capacidade_display,
            'id': r.aula.id,
        })

    for pt in reservas_pt:
        eventos.append({
            'tipo': 'pt',
            'data': pt.horario,
            'nome': 'Sessão PT',
            'duracao': pt.duracao_min,
            'instrutor': pt.instrutor.display_name,
            'id': pt.id,
        })

    eventos.sort(key=lambda e: e['data'])

    context = {'eventos': eventos}
    return render(request, 'aluno/minhas_reservas.html', context)

@require_POST
@login_required
def cancelar_pt(request, pt_id):
    pt = get_object_or_404(PTSession, id=pt_id, aluno=request.user)
    pt.delete()
    messages.success(request, "Sessão de PT cancelada com sucesso!")
    return redirect('minhas_reservas')


@login_required
def minhas_aulas(request):
    if request.user.role != 'instrutor':
        return redirect('horario_aulas')

    agora = timezone.localtime()  # garante o timezone local

    # Aulas futuras do instrutor
    aulas = Class.objects.filter(
        instrutor=request.user,
        horario_inicio__gte=agora
    ).select_related('instrutor').order_by('horario_inicio')

    # Sessões PT futuras do instrutor
    pt_sessions = PTSession.objects.filter(
        instrutor=request.user,
        horario__gte=agora
    ).select_related('aluno').order_by('horario')

    # Combinar ambas num único array, com timestamps para ordenar
    eventos = []

    for a in aulas:
        eventos.append({
            'tipo': 'aula',
            'data': a.horario_inicio,
            'nome': a.nome,
            'duracao': a.duracao_min,
            'capacidade': a.capacidade_display,
            'aluno': None,
        })

    for pt in pt_sessions:
        eventos.append({
            'tipo': 'pt',
            'data': pt.horario,
            'nome': f'Treino PT com {pt.aluno.display_name}',
            'duracao': pt.duracao_min,
            'capacidade': None,
            'aluno': pt.aluno.display_name,
        })

    # Ordenar cronologicamente
    eventos.sort(key=lambda e: e['data'])

    context = {
        'eventos': eventos,
    }
    return render(request, 'instrutor/minhas_aulas.html', context)

# ----------------------------
# Pagamentos (aluno)
# ----------------------------
from django.db.models import Sum

VALORES_SUBSCRICAO = {
    'estudante': Decimal('30.00'),
    'adulto': Decimal('45.00'),
    'familiar': Decimal('90.00'),
    'senior': Decimal('30.00'),
}

LATE_FEE = Decimal('5.00')  # multa
DUE_DAY = 10  # dia limite

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def _mes_ref(dt: date) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"

def _parse_mes_ref(mes_ref: str):
    """
    Aceita:
      - 'YYYY-MM'
      - 'Janeiro 2026' (para não crashar caso existam valores antigos errados)
    """
    if not mes_ref:
        return None

    s = str(mes_ref).strip()

    # Caso normal: YYYY-MM
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 2:
            try:
                y = int(parts[0])
                m = int(parts[1])
                return date(y, m, 1)
            except ValueError:
                return None

    # Caso legacy: "Janeiro 2026"
    tokens = s.split()
    if len(tokens) >= 2:
        try:
            ano = int(tokens[-1])
            nome_mes = " ".join(tokens[:-1]).strip().lower()
            mapa = {v.lower(): k for k, v in MESES_PT.items()}
            if nome_mes in mapa:
                return date(ano, mapa[nome_mes], 1)
        except ValueError:
            return None

    return None

def _mes_label(mes_ref: str) -> str:
    dt = _parse_mes_ref(mes_ref)
    if not dt:
        return mes_ref
    return f"{MESES_PT[dt.month]} {dt.year}"

def due_date_for_month(month_start: date) -> date:
    return month_start.replace(day=DUE_DAY)

def _valor_mensalidade(user: User) -> Decimal:
    return VALORES_SUBSCRICAO.get(user.tipo_subscricao, Decimal('45.00'))

def _user_tem_subscricao_ativa_no_mes(user: User, mes_inicio: date) -> bool:
    """
    True se o user ainda tem subscrição ativa para esse mês.
    - Se não existir cancel_effective_from -> ativo
    - Se existir -> ativo apenas para meses ANTES do effective_from
    """
    efetivo = getattr(user, "cancel_effective_from", None)
    if efetivo:
        return mes_inicio < efetivo
    return True

def _first_day_of_month(d: date) -> date:
    return d.replace(day=1)

def _first_day_next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)

def _iter_months(start_month: date, end_month: date):
    m = _first_day_of_month(start_month)
    end_m = _first_day_of_month(end_month)
    while m <= end_m:
        yield m
        m = _first_day_next_month(m)

def _user_data_entrada(user: User) -> date:
    # usa date_joined como "data de entrada" (como tens no perfil)
    dj = user.date_joined
    if isinstance(dj, datetime):
        return timezone.localtime(dj).date()
    return dj if isinstance(dj, date) else timezone.localdate()


@login_required
def pagamentos(request):
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    user = request.user
    hoje = timezone.localdate()

    data_entrada = _user_data_entrada(user)
    mes_inicio = _first_day_of_month(data_entrada)
    mes_atual = _first_day_of_month(hoje)

    valor_mensalidade = _valor_mensalidade(user)
    cancel_effective_from = getattr(user, "cancel_effective_from", None)

    # 1) Mapear pagamentos já existentes (só os que conseguimos interpretar como mês)
    payments_by_key = {}
    for p in Payment.objects.filter(usuario=user):
        dt = _parse_mes_ref(p.mes_referencia)
        if not dt:
            continue
        key = _mes_ref(dt)
        # só consideramos a partir do mês de entrada
        if dt < mes_inicio:
            continue
        payments_by_key[key] = p

    # 2) Garantir pagamentos desde o mês de entrada até ao mês atual (inclusive)
    for m in _iter_months(mes_inicio, mes_atual):
        if not _user_tem_subscricao_ativa_no_mes(user, m):
            # se a subscrição ficou inativa a partir daqui, os meses seguintes também não contam
            break

        key = _mes_ref(m)
        if key not in payments_by_key:
            p = Payment.objects.create(
                usuario=user,
                mes_referencia=key,
                valor=valor_mensalidade,
                data_limite=due_date_for_month(m),
                status='por_pagar',
            )
            payments_by_key[key] = p

    # 3) Construir lista ordenada (mes_inicio -> mes_atual)
    pagamentos_periodo = []
    for m in _iter_months(mes_inicio, mes_atual):
        key = _mes_ref(m)
        if key in payments_by_key:
            pagamentos_periodo.append(payments_by_key[key])

    # 4) Aplicar multa (uma vez) aos pagamentos em atraso ainda por pagar
    # regra: se hoje > data_limite, e valor ainda == mensalidade base, então soma 5€
    for p in pagamentos_periodo:
        if p.status == 'por_pagar' and hoje > p.data_limite:
            if p.valor == valor_mensalidade:
                p.valor = p.valor + LATE_FEE
                p.save(update_fields=['valor'])

        # atributos extra para o template (não vão para BD)
        p.mes_label = _mes_label(p.mes_referencia)
        p.em_atraso = (p.status == 'por_pagar' and hoje > p.data_limite)

    mes_atual_key = _mes_ref(mes_atual)

    pagamento_atual = payments_by_key.get(mes_atual_key, None)
    if pagamento_atual:
        pagamento_atual.mes_label = _mes_label(pagamento_atual.mes_referencia)
        pagamento_atual.em_atraso = (pagamento_atual.status == 'por_pagar' and hoje > pagamento_atual.data_limite)

    # Pagamentos em atraso: meses < mes_atual e por pagar
    pagamentos_em_atraso = []
    for p in pagamentos_periodo:
        dt = _parse_mes_ref(p.mes_referencia)
        if dt and dt < mes_atual and p.status == 'por_pagar':
            pagamentos_em_atraso.append(p)

    # Histórico: pagos (desde a entrada)
    historico = Payment.objects.filter(
        usuario=user,
        status='pago',
        mes_referencia__gte=_mes_ref(mes_inicio),
    ).order_by('-mes_referencia')

    total_pago = historico.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    # 5) Futuros (preview): próximos 2 meses (não cria na BD)
    futuros = []
    m = _first_day_next_month(mes_atual)
    for _ in range(2):
        if not _user_tem_subscricao_ativa_no_mes(user, m):
            break
        futuros.append({
            'mes_key': _mes_ref(m),
            'mes_label': _mes_label(_mes_ref(m)),
            'data_limite': due_date_for_month(m),
            'valor': valor_mensalidade,
        })
        m = _first_day_next_month(m)

    context = {
        'valor_mensalidade': valor_mensalidade,
        'cancel_effective_from': cancel_effective_from,

        'pagamentos_em_atraso': pagamentos_em_atraso,
        'pagamento_atual': pagamento_atual,
        'futuros': futuros,

        'historico': historico,
        'total_pago': total_pago,
    }

    return render(request, 'aluno/pagamentos.html', context)


@require_POST
@login_required
def pagar_pagamento(request, pagamento_id):
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    pagamento = get_object_or_404(Payment, id=pagamento_id, usuario=request.user)

    if pagamento.status != 'pago':
        hoje = timezone.localdate()
        valor_mensalidade = _valor_mensalidade(request.user)

        # se estiver em atraso e ainda não tiver multa aplicada (heurística simples)
        if hoje > pagamento.data_limite and pagamento.valor == valor_mensalidade:
            pagamento.valor = pagamento.valor + LATE_FEE

        pagamento.status = 'pago'
        pagamento.save(update_fields=['status', 'valor'])
        messages.success(request, "Pagamento marcado como pago ✅")

    return redirect('pagamentos')


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
    # - depois do 15 -> show cancela no 1º dia do mês seguinte ao próximo
    if hoje.day <= 15:
        efetivo = _first_day_next_month(hoje)
    else:
        efetivo = _first_day_next_month(_first_day_next_month(hoje))

    request.user.cancel_requested_at = timezone.now()
    request.user.cancel_effective_from = efetivo
    request.user.save(update_fields=['cancel_requested_at', 'cancel_effective_from'])

    # apaga pagamentos futuros guardados na BD (se existirem)
    Payment.objects.filter(
        usuario=request.user,
        mes_referencia__gte=_mes_ref(efetivo)
    ).delete()

    messages.success(request, f"Subscrição cancelada. Fica inativa a partir de {efetivo.strftime('%d/%m/%Y')}.")
    return redirect('pagamentos')


@require_POST
@login_required
def reativar_subscricao(request):
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    if not hasattr(request.user, "cancel_effective_from"):
        messages.error(request, "O modelo User ainda não tem os campos de cancelamento (faz a migration primeiro).")
        return redirect('pagamentos')

    if not request.user.cancel_effective_from:
        messages.info(request, "Não existe nenhum cancelamento agendado.")
        return redirect('pagamentos')

    request.user.cancel_requested_at = None
    request.user.cancel_effective_from = None
    request.user.save(update_fields=['cancel_requested_at', 'cancel_effective_from'])

    messages.success(request, "Subscrição reativada com sucesso ✅")
    return redirect('pagamentos')

@login_required
def perfil_redirect(request):
    """Redireciona o user para o perfil certo"""
    if request.user.role == 'instrutor':
        return redirect('perfil_instrutor')
    return redirect('perfil_aluno')


@login_required
def perfil_aluno(request):
    """Página de perfil do aluno"""
    if request.user.role != 'cliente':
        return redirect('perfil_instrutor')

    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Buscar todas as reservas confirmadas do aluno neste mês
    reservas_mes = Booking.objects.filter(
        usuario=request.user,
        aula__horario_inicio__date__gte=inicio_mes,
        aula__horario_inicio__date__lte=fim_mes,
        status=True
    ).select_related('aula')

    total_aulas = reservas_mes.count()

    # Contagem por tipo de aula
    contagem_por_tipo = Counter(r.aula.nome for r in reservas_mes)

    aula_mais_frequente = max(contagem_por_tipo, key=contagem_por_tipo.get) if contagem_por_tipo else None

    # Preparar dados para gráfico
    labels = list(contagem_por_tipo.keys())
    data = list(contagem_por_tipo.values())

    context = {
        'user': request.user,
        'total_aulas': total_aulas,
        'aula_mais_frequente': aula_mais_frequente,
        'labels': labels,
        'data': data,
    }

    return render(request, 'aluno/perfil.html', context)


@login_required
def perfil_instrutor(request):
    """Página de perfil do instrutor"""
    if request.user.role != 'instrutor':
        return redirect('perfil_aluno')

    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Upload de nova foto de perfil
    if request.method == 'POST' and request.FILES.get('foto_perfil'):
        request.user.foto_perfil = request.FILES['foto_perfil']
        request.user.save()
        messages.success(request, "Foto de perfil atualizada com sucesso!")
        return redirect('perfil_instrutor')

    # Aulas deste mês
    aulas_mes = Class.objects.filter(
        instrutor=request.user,
        horario_inicio__date__gte=inicio_mes,
        horario_inicio__date__lte=fim_mes,
    ).order_by('horario_inicio')

    total_aulas = aulas_mes.count()

    # Participações por aula individual (não somadas por nome)
    participacoes = (
        Booking.objects.filter(aula__in=aulas_mes, status=True)
        .values('aula__nome', 'aula__horario_inicio')
        .annotate(total=Count('id'))
        .order_by('-total')  # aula com mais alunos primeiro
    )

    # Labels detalhados com data/hora
    labels = [
        f"{p['aula__nome']} ({p['aula__horario_inicio'].strftime('%d/%m %H:%M')})"
        for p in participacoes
    ]
    data = [p['total'] for p in participacoes]

    total_participantes = sum(data)

    # Aula mais popular
    aula_mais_popular = None
    if participacoes:
        aula_top = participacoes[0]
        aula_mais_popular = f"{aula_top['aula__nome']} ({aula_top['aula__horario_inicio'].strftime('%d/%m %H:%M')})"

    context = {
        'user': request.user,
        'total_aulas': total_aulas,
        'total_participantes': total_participantes,
        'labels': labels,
        'data': data,
        'aula_mais_popular': aula_mais_popular,
    }

    return render(request, 'instrutor/perfil.html', context)



def signup_cliente(request):
    if request.method == 'POST':
        form = ClienteSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'cliente'
            user.save()

            # Fazer login automático após o registo
            login(request, user)

            # Redirecionar para o dashboard do aluno
            return redirect('aluno_dashboard')
    else:
        form = ClienteSignupForm()
    return render(request, 'auth/signup_cliente.html', {'form': form})


def signup_instrutor(request):
    if request.method == 'POST':
        form = InstrutorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'instrutor'
            user.is_staff = True  # opcional para aceder ao admin
            user.save()

            # Fazer login automático após o registo
            login(request, user)

            # Redirecionar para o dashboard do instrutor
            return redirect('instrutor_dashboard')
    else:
        form = InstrutorSignupForm()
    return render(request, 'auth/signup_instrutor.html', {'form': form})


@login_required
def marcar_consulta(request, instrutor_id):
    # busca o instrutor
    instrutor = get_object_or_404(User, id=instrutor_id, role='instrutor')

    # todos os horários futuros do instrutor ocupados com aulas
    agora = timezone.now()
    aulas_ocupadas = Class.objects.filter(
        instrutor=instrutor,
        horario_inicio__gte=agora
    ).values_list('horario_inicio', flat=True)

    # horários já reservados como PT
    pt_ocupados = PTSession.objects.filter(
        instrutor=instrutor,
        horario__gte=agora
    ).values_list('horario', flat=True)

    # combinar horários ocupados
    ocupados = set(aulas_ocupadas).union(set(pt_ocupados))

    # gerar próximos 7 dias de horários de 1h para marcar PT
    disponiveis = []
    for dia in range(7):
        data = agora + timedelta(days=dia)
        for hora in range(8, 20):  # exemplo: 8h-20h
            slot = data.replace(hour=hora, minute=0, second=0, microsecond=0)
            if slot not in ocupados:
                disponiveis.append(slot)

    if request.method == 'POST':
        horario_selecionado = request.POST.get('horario')
        horario_dt = timezone.datetime.fromisoformat(horario_selecionado)
        # criar PTSession
        PTSession.objects.create(
            aluno=request.user,
            instrutor=instrutor,
            horario=horario_dt
        )
        messages.success(request, f"Consulta marcada com {instrutor.display_name} em {horario_dt.strftime('%d/%m/%Y %H:%M')}")
        return redirect('aluno_dashboard')

    return render(request, 'aluno/marcar_consulta.html', {
        'instrutor': instrutor,
        'disponiveis': disponiveis
    })


@login_required
def instrutor_horario(request):
    if request.user.role != 'instrutor':
        return redirect('horario_aulas')

    agora = timezone.now()

    # Apenas aulas futuras
    aulas = Class.objects.filter(
        instrutor=request.user,
        horario_inicio__gte=agora
    ).order_by('horario_inicio')

    if request.method == 'POST':
        nome = request.POST.get('nome_aula')
        horario = request.POST.get('horario_inicio')
        duracao = int(request.POST.get('duracao', 60))
        capacidade = int(request.POST.get('capacidade_max', 20))

        Class.objects.create(
            nome=nome,
            instrutor=request.user,
            horario_inicio=horario,
            duracao_min=duracao,
            capacidade_max=capacidade
        )
        messages.success(request, "Aula criada com sucesso!")
        return redirect('instrutor_horario')

    return render(request, 'instrutor/horario_gerir.html', {'aulas': aulas})


@login_required
def listar_instrutores(request):
    instrutores = User.objects.filter(role='instrutor')
    return render(request, 'aluno/lista_instrutores.html', {'instrutores': instrutores})



@login_required
def index(request):
    """
    Página index pedida no enunciado:
    - links para cada entidade
    - número de elementos em cada tabela
    Nota: para evitar “leaks”, deixamos só para staff/instrutor/admin.
    """
    if not request.user.is_staff:
        # manda para o dashboard normal de cada role
        if getattr(request.user, "role", None) == "instrutor":
            return redirect("instrutor_dashboard")
        return redirect("aluno_dashboard")

    # Contagens principais
    total_users = User.objects.count()
    total_clientes = User.objects.filter(role="cliente").count()
    total_instrutores = User.objects.filter(role="instrutor").count()

    total_classes = Class.objects.count()
    total_bookings = Booking.objects.count()
    total_bookings_ativas = Booking.objects.filter(status=True).count()

    total_payments = Payment.objects.count()
    total_payments_pagos = Payment.objects.filter(status="pago").count()
    total_payments_pendentes = Payment.objects.filter(status="por_pagar").count()

    total_ptsessions = PTSession.objects.count()

    # Links diretos para o Django Admin (changelists)
    # admin:<app_label>_<modelname>_changelist
    cards = [
        {
            "label": "Utilizadores (total)",
            "count": total_users,
            "meta": f"Clientes: {total_clientes} | Instrutores: {total_instrutores}",
            "url": reverse("admin:core_user_changelist"),
        },
        {
            "label": "Aulas (Classes)",
            "count": total_classes,
            "meta": "Gerir aulas no admin",
            "url": reverse("admin:core_class_changelist"),
        },
        {
            "label": "Reservas (Bookings)",
            "count": total_bookings,
            "meta": f"Ativas: {total_bookings_ativas}",
            "url": reverse("admin:core_booking_changelist"),
        },
        {
            "label": "Pagamentos (Payments)",
            "count": total_payments,
            "meta": f"Pagos: {total_payments_pagos} | Pendentes: {total_payments_pendentes}",
            "url": reverse("admin:core_payment_changelist"),
        },
        {
            "label": "Sessões PT (PTSession)",
            "count": total_ptsessions,
            "meta": "Sessões de Personal Training",
            "url": reverse("admin:core_ptsession_changelist"),
        },
    ]

    context = {
        "cards": cards,
        "admin_index_url": reverse("admin:index"),
    }
    return render(request, "index.html", context)
