from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'profile_photo_preview',
        'profile_photo',
        'first_name', 
        'last_name', 
        'phone', 
        'birthdate',
        'newsletter',
        'order_updates', 
        'promotions',
        'language',
        'currency',
    )
    readonly_fields = ('profile_photo_preview',)
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_photo.url
            )
        return "No photo"
    
    profile_photo_preview.short_description = 'Profile Photo Preview'


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # Display fields in user list
    list_display = (
        'email', 
        'get_full_name', 
        'is_staff', 
        'is_active',
        'date_joined',
    )
    
    list_filter = (
        'is_staff', 
        'is_active', 
        'date_joined',
        'is_superuser',  # Added superuser filter
    )
    
    # Fields for editing user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': (
                'is_staff', 
                'is_active', 
                'is_superuser', 
                'groups', 
                'user_permissions'
            ),
            'classes': ('collapse',)  # Make permissions collapsible
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)  # Make dates collapsible
        }),
    )
    
    # Fields for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'password1', 
                'password2', 
                'is_staff', 
                'is_active'
            )}
        ),
    )
    
    search_fields = ('email', 'profile__first_name', 'profile__last_name')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')
    
    # Add UserProfile as inline
    inlines = [UserProfileInline]
    
    def get_full_name(self, obj):
        """Display full name from profile in admin list"""
        # Use try-except to handle cases where profile might not exist
        try:
            return obj.profile.get_full_name()
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist (safety fallback)
            UserProfile.objects.create(user=obj)
            return obj.profile.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def get_inline_instances(self, request, obj=None):
        """Only show inline when editing existing user"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    def get_queryset(self, request):
        """Optimize queryset to prefetch related profile data"""
        return super().get_queryset(request).select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model"""
    
    list_display = (
        'user',
        'get_full_name',
        'phone',
        'has_photo',
        'newsletter',
        'language',
        'created_at',
    )
    
    list_filter = (
        'newsletter',
        'order_updates',
        'promotions',
        'language',
        'currency',
        'created_at',
    )
    
    search_fields = (
        'user__email',
        'first_name',
        'last_name',
        'phone',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'profile_photo_preview',
        'user',  # Make user read-only to prevent accidental changes
    )
    
    fieldsets = (
        (_('User Information'), {
            'fields': (
                'user',
                'profile_photo_preview',
                'profile_photo',
            )
        }),
        (_('Personal Information'), {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'birthdate',
            )
        }),
        (_('Preferences'), {
            'fields': (
                'newsletter',
                'order_updates',
                'promotions',
                'language',
                'currency',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Add some useful admin actions
    actions = ['enable_newsletter', 'disable_newsletter']
    
    def enable_newsletter(self, request, queryset):
        """Admin action to enable newsletter for selected profiles"""
        updated = queryset.update(newsletter=True)
        self.message_user(request, f'Enabled newsletter for {updated} profiles.')
    enable_newsletter.short_description = "Enable newsletter for selected profiles"
    
    def disable_newsletter(self, request, queryset):
        """Admin action to disable newsletter for selected profiles"""
        updated = queryset.update(newsletter=False)
        self.message_user(request, f'Disabled newsletter for {updated} profiles.')
    disable_newsletter.short_description = "Disable newsletter for selected profiles"
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def has_photo(self, obj):
        return obj.has_photo
    has_photo.boolean = True
    has_photo.short_description = 'Has Photo'
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="150" height="150" style="border-radius: 8px; object-fit: cover;" />',
                obj.profile_photo.url
            )
        return "No profile photo uploaded"
    profile_photo_preview.short_description = 'Profile Photo Preview'
    
    def get_queryset(self, request):
        """Optimize queryset to select related user data"""
        return super().get_queryset(request).select_related('user')


# Register CustomUser with the enhanced admin
# Note: We don't need to register CustomUser again if it's already registered in the class
# admin.site.register(CustomUser, CustomUserAdmin)  # This line is redundant