from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('aulas/', views.ClassListView.as_view(), name='class_list'),
    path('aulas/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
]
