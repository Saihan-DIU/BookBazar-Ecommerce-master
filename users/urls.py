# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Class-based view
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Function-based views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]