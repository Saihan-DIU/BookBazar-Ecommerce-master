from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
import os


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


def user_profile_photo_path(instance, filename):
    """File will be uploaded to MEDIA_ROOT/users/user_<id>/profile_photos/<filename>"""
    ext = filename.split('.')[-1]
    filename = f'profile_photo.{ext}'
    return f'users/user_{instance.user.id}/profile_photos/{filename}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path, 
        blank=True, 
        null=True
    )
    
    # Preferences
    newsletter = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    promotions = models.BooleanField(default=False)
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
    ]
    language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES, 
        default='en'
    )
    
    CURRENCY_CHOICES = [
        ('usd', 'USD ($)'),
        ('eur', 'EUR (€)'),
        ('gbp', 'GBP (£)'),
    ]
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='usd'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
    
    def get_full_name(self):
        """Get user's full name or fallback to email username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            # Extract username from email (part before @)
            return self.user.email.split('@')[0].title()
    
    def get_display_name(self):
        """Get display name for UI"""
        if self.first_name:
            return self.first_name
        else:
            return self.user.email.split('@')[0].title()
    
    def delete_photo(self):
        """Delete the profile photo file from filesystem"""
        if self.profile_photo:
            if os.path.isfile(self.profile_photo.path):
                os.remove(self.profile_photo.path)
            self.profile_photo = None
            self.save()
    
    @property
    def has_photo(self):
        """Check if user has a profile photo"""
        return bool(self.profile_photo)
    
    @property
    def member_since(self):
        """Get how long the user has been a member"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(self.user.date_joined).split(',')[0]


def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a UserProfile when a new CustomUser is created
    """
    if created:
        UserProfile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save UserProfile when CustomUser is saved
    """
    instance.profile.save()


# Connect the signals
post_save.connect(create_user_profile, sender=CustomUser)
post_save.connect(save_user_profile, sender=CustomUser)