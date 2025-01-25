from django.urls import path
from .views import edit_profile
from . import views

urlpatterns = [
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
]