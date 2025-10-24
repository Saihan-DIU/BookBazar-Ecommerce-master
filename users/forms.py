from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import UserProfile
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email address'
        })
    )
    
    class Meta:
        model = get_user_model()
        fields = ("email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to password fields for consistency
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]  # Use email as username
        if commit:
            user.save()
            # REMOVE the manual profile creation - signals will handle it
            # UserProfile.objects.create(user=user)
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return emails

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in admin"""
    
    class Meta:
        model = get_user_model()
        fields = ('email', 'password')


class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(
        disabled=True, 
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'phone', 'birthdate', 'profile_photo',
            'newsletter', 'order_updates', 'promotions', 'language', 'currency'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Enter your last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+1 (555) 000-0000'
            }),
            'birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'file-input',
                'accept': 'image/*'
            }),
            'language': forms.Select(attrs={'class': 'form-input'}),
            'currency': forms.Select(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
        
        # Add CSS classes to checkbox fields
        for field_name in ['newsletter', 'order_updates', 'promotions']:
            self.fields[field_name].widget.attrs.update({'class': 'checkbox'})
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            # Basic phone validation - remove non-digit characters and check length
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) < 10:
                raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone
    
    def clean_birthdate(self):
        birthdate = self.cleaned_data.get('birthdate')
        if birthdate:
            from datetime import date
            today = date.today()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            if age < 13:
                raise forms.ValidationError("You must be at least 13 years old to use this service.")
            if age > 120:
                raise forms.ValidationError("Please enter a valid birthdate.")
        return birthdate
    
    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # Validate file size (5MB limit)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Profile photo must be less than 5MB.")
            
            # Validate file type
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            extension = photo.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise forms.ValidationError(
                    "Unsupported file format. Please upload JPG, PNG, GIF, or WebP."
                )
        return photo