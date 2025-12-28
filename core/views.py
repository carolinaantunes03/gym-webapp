from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Class, Booking, Payment

from .forms import LoginForm
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

    # Calcular próximos/dias anteriores
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

@login_required
def pagamentos(request):
    # Apenas alunos podem ver
    if request.user.role != 'cliente':
        return redirect('horario_aulas')

    # Obter todos os pagamentos do aluno
    pagamentos_aluno = Payment.objects.filter(usuario=request.user).order_by('mes_referencia')

    # Dicionário com valores por tipo de subscrição
    valores_subscricao = {
        'estudante': 30.00,
        'adulto': 45.00,
        'familiar': 90.00,
        'senior': 30.00,
    }

    context = {
        'pagamentos': pagamentos_aluno,
        'valor_mensalidade': valores_subscricao.get(request.user.tipo_subscricao, 45.00)
    }

    return render(request, 'aluno/pagamentos.html', context)
