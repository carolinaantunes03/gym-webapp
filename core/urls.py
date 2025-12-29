from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('aluno/dashboard/', views.aluno_dashboard, name='aluno_dashboard'),
    path('instrutor/dashboard/', views.instrutor_dashboard, name='instrutor_dashboard'),
    path('horario/', views.horario_aulas, name='horario_aulas'),
    path('reserva/<int:aula_id>/', views.toggle_reserva, name='toggle_reserva'),
    path('minhas-reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('minhas-aulas/', views.minhas_aulas, name='minhas_aulas'),
    path('pagamentos/', views.pagamentos, name='pagamentos'),
    path('pagamentos/pagar/<int:pagamento_id>/', views.pagar_pagamento, name='pagar'),
    path('pagamentos/cancelar/', views.cancelar_subscricao, name='cancelar_subscricao'),




]