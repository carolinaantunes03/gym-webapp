from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, ListView, DetailView
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
