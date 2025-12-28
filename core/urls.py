from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('aulas/', views.ClassListView.as_view(), name='class_list'),
    path('aulas/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('reservar/<int:pk>/', views.BookingCreateView.as_view(), name='book_class'),
    path('pagamentos/', views.PaymentListView.as_view(), name='payment_list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
