from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

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
    path('perfil/', views.perfil_redirect, name='perfil_redirect'),
    path('perfil/aluno/', views.perfil_aluno, name='perfil_aluno'),
    path('perfil/instrutor/', views.perfil_instrutor, name='perfil_instrutor'),
    path('signup/cliente/', views.signup_cliente, name='signup_cliente'),
    path('signup/instrutor/', views.signup_instrutor, name='signup_instrutor'),
    path('aluno/instrutores/', views.listar_instrutores, name='listar_instrutores'),
    path('aluno/marcar/<int:instrutor_id>/', views.marcar_consulta, name='marcar_consulta'),
    path('minhas-reservas/cancelar-pt/<int:pt_id>/', views.cancelar_pt, name='cancelar_pt'),
    path('instrutor/horario/gerir/', views.instrutor_horario, name='instrutor_horario'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)