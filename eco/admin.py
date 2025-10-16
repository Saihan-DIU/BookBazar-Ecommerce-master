from django.contrib import admin
from .models import (
    Category, 
    Book, 
    OrderItem, 
    Order, 
    Address, 
    Payment, 
    Coupon, 
    Refund, 
    UserProfile, 
    Wishlist
)

class BookAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'author', 
        'price', 
        'featured',  # ADDED: Featured field
        'category', 
        'is_available', 
        'stock_quantity'
    ]
    list_filter = [
        'featured',  # ADDED: Filter by featured status
        'category', 
        'author', 
        'is_available'
    ]
    list_editable = [
        'featured',  # ADDED: Allow quick editing
        'price',
        'is_available',
        'stock_quantity'
    ]
    search_fields = ['title', 'author', 'isbn', 'isbn13']
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['created_at', 'updated_at']
    
    # ADDED: Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'author', 'additional_authors', 'isbn', 'isbn13', 'slug'
            )
        }),
        ('Categorization', {
            'fields': (
                'category', 'genre', 'format_type', 'condition'
            )
        }),
        ('Publishing & Pricing', {
            'fields': (
                'publisher', 'publication_date', 'edition', 'pages', 'language',
                'price', 'discount_price', 'featured'  # ADDED: Featured field
            )
        }),
        ('Media & Content', {
            'fields': (
                'cover_image', 'additional_images', 'description', 'excerpt'
            )
        }),
        ('Inventory & Status', {
            'fields': (
                'stock_quantity', 'is_available', 'label1', 'label2', 'label3'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_display', 'quantity', 'ordered']
    list_filter = ['ordered', 'user']
    
    def book_display(self, obj):
        return obj.item.title if obj.item else "No Book"
    book_display.short_description = 'Book'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', 'ordered_date', 'get_total', 'being_delivered', 'received']
    list_filter = ['ordered', 'ordered_date', 'being_delivered', 'received']
    search_fields = ['user__username', 'ref_code']

class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'country', 'zip_code', 'address_type', 'default']
    list_filter = ['country', 'address_type', 'default']
    search_fields = ['user__username', 'street_address', 'zip_code']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'stripe_charge_id']

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'amount']
    search_fields = ['code']

class RefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'reason', 'accepted', 'email']
    list_filter = ['accepted']
    search_fields = ['order__ref_code', 'email']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'stripe_customer_id', 'one_click_purchasing']
    search_fields = ['user__username']

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_display', 'added_date']
    list_filter = ['added_date']
    search_fields = ['user__username']
    
    def book_display(self, obj):
        return obj.item.title if obj.item else "No Book"
    book_display.short_description = 'Book'

# Register your models here
admin.site.register(Category, CategoryAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Wishlist, WishlistAdmin)