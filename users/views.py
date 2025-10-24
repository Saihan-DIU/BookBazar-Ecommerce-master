# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm  # Built-in form
from django.views import generic
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, ProfileEditForm
from .models import UserProfile

# Class-based view for registration (keep your existing one)
class RegisterView(generic.CreateView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('eco:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome {user.email}! Your account has been created successfully.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('eco:home')
        return super().dispatch(request, *args, **kwargs)

# Function-based views for other authentication
def login_view(request):
    """User login view using built-in AuthenticationForm"""
    if request.user.is_authenticated:
        return redirect('eco:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')  # This will be email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.email}!')
                return redirect('eco:home')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    if request.user.is_authenticated:
        messages.info(request, 'You have been logged out.')
    logout(request)
    return redirect('eco:home')

@login_required
def profile_view(request):
    """User profile view"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'categories': [],  # Add empty categories to avoid template errors
        'featured_books': [],  # Add empty featured_books to avoid template errors
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit_view(request):
    """Edit user profile view with photo upload"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Handle photo removal
            if request.POST.get('remove_photo') == 'true':
                if profile.profile_photo:
                    profile.profile_photo.delete(save=False)
                    profile.profile_photo = None
            
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=profile)
    
    context = {
        'user': request.user,
        'categories': [],
        'featured_books': [],
        'form': form,
    }
    return render(request, 'users/profile_edit.html', context)

@login_required
def change_password_view(request):
    """Change password view"""
    context = {
        'user': request.user,
        'categories': [],
        'featured_books': [],
    }
    return render(request, 'users/change_password.html', context)