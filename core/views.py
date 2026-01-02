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
from django.db.models import Count

from .forms import ClienteSignupForm, InstrutorSignupForm
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from .models import PTSession, User, Class

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


