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
        'discounted_price',
        'featured',
        'category', 
        'is_available', 
        'stock_status',
        'stock_quantity'
    ]
    list_filter = [
        'featured',
        'category', 
        'author', 
        'is_available',
        'genre',
        'format_type',
        'condition'
    ]
    list_editable = [
        'featured',
        'price',
        'is_available',
        'stock_quantity'
    ]
    search_fields = [
        'title', 
        'author', 
        'additional_authors', 
        'isbn', 
        'isbn13', 
        'publisher', 
        'genre',
        'description'
    ]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['created_at', 'updated_at']
    
    # Custom actions for bulk operations
    actions = [
        'make_featured', 
        'make_unfeatured', 
        'mark_available', 
        'mark_unavailable',
        'increase_stock',
        'clear_stock'
    ]
    
    # Fieldsets for better organization
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
                'price', 'discount_price', 'featured'
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
    
    # Custom display methods
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return "❌ Out of Stock"
        elif obj.stock_quantity < 5:
            return f"⚠️ Low ({obj.stock_quantity})"
        elif obj.stock_quantity < 10:
            return f"🔶 Medium ({obj.stock_quantity})"
        else:
            return f"✅ Good ({obj.stock_quantity})"
    stock_status.short_description = 'Stock Status'
    stock_status.admin_order_field = 'stock_quantity'
    
    def discounted_price(self, obj):
        if obj.discount_price and obj.discount_price < obj.price:
            return f"${obj.discount_price} (Save ${obj.price - obj.discount_price:.2f})"
        return "—"
    discounted_price.short_description = 'Discounted Price'
    
    # Bulk action methods
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} books marked as featured.')
    make_featured.short_description = "Mark selected books as featured"
    
    def make_unfeatured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} books marked as not featured.')
    make_unfeatured.short_description = "Mark selected books as not featured"
    
    def mark_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} books marked as available.')
    mark_available.short_description = "Mark selected books as available"
    
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} books marked as unavailable.')
    mark_unavailable.short_description = "Mark selected books as unavailable"
    
    def increase_stock(self, request, queryset):
        for book in queryset:
            book.stock_quantity += 10
            book.save()
        self.message_user(request, f'Increased stock by 10 for {queryset.count()} books.')
    increase_stock.short_description = "Increase stock by 10 for selected books"
    
    def clear_stock(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, f'Cleared stock for {updated} books.')
    clear_stock.short_description = "Clear stock (set to 0) for selected books"

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'book_count']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']
    
    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Number of Books'

class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'book_display', 
        'quantity', 
        'get_final_price', 
        'ordered'
    ]
    list_filter = ['ordered', 'user']
    search_fields = ['user__username', 'item__title', 'item__author']
    
    def book_display(self, obj):
        return f"{obj.item.title} by {obj.item.author}" if obj.item else "No Book"
    book_display.short_description = 'Book'
    
    def get_final_price(self, obj):
        if obj.item.discount_price:
            return f"${obj.get_total_discount_item_price():.2f}"
        return f"${obj.get_total_item_price():.2f}"
    get_final_price.short_description = 'Total Price'

class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'ordered', 
        'ordered_date', 
        'get_total', 
        'being_delivered', 
        'received',
        'refund_requested',
        'refund_granted'
    ]
    list_filter = [
        'ordered', 
        'ordered_date', 
        'being_delivered', 
        'received',
        'refund_requested',
        'refund_granted'
    ]
    search_fields = ['user__username', 'ref_code', 'shipping_address__street_address']
    list_editable = ['being_delivered', 'received', 'refund_granted']
    readonly_fields = ['ordered_date', 'start_date']
    
    actions = ['mark_delivered', 'mark_received', 'grant_refunds']
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(being_delivered=True)
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_received(self, request, queryset):
        updated = queryset.update(received=True)
        self.message_user(request, f'{updated} orders marked as received.')
    mark_received.short_description = "Mark selected orders as received"
    
    def grant_refunds(self, request, queryset):
        updated = queryset.update(refund_granted=True)
        self.message_user(request, f'{updated} orders granted refunds.')
    grant_refunds.short_description = "Grant refunds for selected orders"

class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'street_address', 
        'apartment_address',
        'country', 
        'zip_code', 
        'address_type', 
        'default'
    ]
    list_filter = ['country', 'address_type', 'default']
    search_fields = [
        'user__username', 
        'street_address', 
        'apartment_address',
        'zip_code'
    ]
    list_editable = ['default']
    
    actions = ['set_default', 'unset_default']
    
    def set_default(self, request, queryset):
        # First unset all defaults for these users
        users = queryset.values_list('user', flat=True).distinct()
        Address.objects.filter(user__in=users).update(default=False)
        # Then set selected as default
        updated = queryset.update(default=True)
        self.message_user(request, f'{updated} addresses set as default.')
    set_default.short_description = "Set selected addresses as default"
    
    def unset_default(self, request, queryset):
        updated = queryset.update(default=False)
        self.message_user(request, f'{updated} addresses unset as default.')
    unset_default.short_description = "Unset selected addresses as default"

class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'amount', 
        'timestamp', 
        'stripe_charge_id'
    ]
    list_filter = ['timestamp']
    search_fields = ['user__username', 'stripe_charge_id']
    readonly_fields = ['timestamp', 'stripe_charge_id']

class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 
        'amount', 
        'active'
    ]
    list_filter = ['active']
    search_fields = ['code']
    list_editable = ['active', 'amount']

class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'order', 
        'reason', 
        'accepted', 
        'email'
    ]
    list_filter = ['accepted']
    search_fields = ['order__ref_code', 'email', 'reason']
    list_editable = ['accepted']
    
    actions = ['accept_refunds', 'reject_refunds']
    
    def accept_refunds(self, request, queryset):
        updated = queryset.update(accepted=True)
        self.message_user(request, f'{updated} refund requests accepted.')
    accept_refunds.short_description = "Accept selected refund requests"
    
    def reject_refunds(self, request, queryset):
        updated = queryset.update(accepted=False)
        self.message_user(request, f'{updated} refund requests rejected.')
    reject_refunds.short_description = "Reject selected refund requests"

class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'stripe_customer_id', 
        'one_click_purchasing',
        'get_orders_count',
        'get_addresses_count'
    ]
    search_fields = ['user__username', 'stripe_customer_id']
    list_filter = ['one_click_purchasing']
    
    def get_orders_count(self, obj):
        return obj.user.order_set.count()
    get_orders_count.short_description = 'Orders Count'
    
    def get_addresses_count(self, obj):
        return obj.user.address_set.count()
    get_addresses_count.short_description = 'Addresses Count'

class WishlistAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'book_display', 
        'get_book_price',
        'get_book_availability'
    ]
    # REMOVED the problematic list_filter - using only simple fields
    search_fields = ['user__username', 'item__title', 'item__author']
    
    def book_display(self, obj):
        return f"{obj.item.title} by {obj.item.author}" if obj.item else "No Book"
    book_display.short_description = 'Book'
    
    def get_book_price(self, obj):
        return f"${obj.item.price:.2f}" if obj.item else "—"
    get_book_price.short_description = 'Price'
    
    def get_book_availability(self, obj):
        if obj.item:
            return "✅ Available" if obj.item.is_available else "❌ Unavailable"
        return "—"
    get_book_availability.short_description = 'Available'

# Register your models
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