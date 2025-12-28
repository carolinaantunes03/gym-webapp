from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Class, Booking, Payment

class HomeView(TemplateView):
    template_name = "home.html"

class ClassListView(ListView):
    model = Class
    template_name = "class_list.html"
    context_object_name = "aulas"

class ClassDetailView(DetailView):
    model = Class
    template_name = "class_detail.html"
    context_object_name = "aula"

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    fields = []  # no form fields — we set everything manually
    template_name = "booking_form.html"

    def post(self, request, *args, **kwargs):
        aula = get_object_or_404(Class, pk=self.kwargs['pk'])
        user = request.user

        # Check if user already booked
        if Booking.objects.filter(usuario=user, aula=aula).exists():
            messages.error(request, "Já reservaste esta aula.")
            return redirect('class_detail', pk=aula.pk)

        # Check capacity
        if Booking.objects.filter(aula=aula, status=True).count() >= aula.capacidade:
            messages.error(request, "A aula está cheia.")
            return redirect('class_detail', pk=aula.pk)

        Booking.objects.create(usuario=user, aula=aula)
        messages.success(request, "Reserva efetuada com sucesso!")
        return redirect('class_detail', pk=aula.pk)

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "payment_list.html"
    context_object_name = "pagamentos"

    def get_queryset(self):
        return Payment.objects.filter(usuario=self.request.user)