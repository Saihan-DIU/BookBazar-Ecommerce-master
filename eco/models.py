from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.conf import settings
from django.template.defaultfilters import slugify
from django.template.defaultfilters import truncatechars
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.html import mark_safe
from django.core.validators import MinValueValidator
from decimal import Decimal

# ==================== BOOKSTORE-SPECIFIC CHOICES ====================

BOOK_GENRES = [
    ('FICTION', 'Fiction'),
    ('NON_FICTION', 'Non-Fiction'),
    ('SCI_FI', 'Science Fiction'),
    ('FANTASY', 'Fantasy'),
    ('MYSTERY', 'Mystery'),
    ('ROMANCE', 'Romance'),
    ('THRILLER', 'Thriller'),
    ('BIOGRAPHY', 'Biography'),
    ('HISTORY', 'History'),
    ('SELF_HELP', 'Self Help'),
    ('SCIENCE', 'Science'),
    ('TECHNOLOGY', 'Technology'),
    ('BUSINESS', 'Business'),
    ('CHILDREN', "Children's Books"),
    ('YOUNG_ADULT', 'Young Adult'),
    ('POETRY', 'Poetry'),
    ('DRAMA', 'Drama'),
    ('CLASSIC', 'Classic Literature'),
    ('HORROR', 'Horror'),
    ('COMICS', 'Comics & Graphic Novels'),
]

BOOK_FORMATS = [
    ('HARDCOVER', 'Hardcover'),
    ('PAPERBACK', 'Paperback'),
    ('EBOOK', 'E-Book'),
    ('AUDIOBOOK', 'Audiobook'),
]

BOOK_CONDITIONS = [
    ('NEW', 'New'),
    ('LIKE_NEW', 'Like New'),
    ('VERY_GOOD', 'Very Good'),
    ('GOOD', 'Good'),
    ('ACCEPTABLE', 'Acceptable'),
]

LABEL_CHOICES = (
    ('N', 'NEW ARRIVAL'),
    ('B', 'BESTSELLER'),
    ('S', 'SPECIAL OFFER'),
    ('P', 'PRE-ORDER'),
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

# ==================== MODELS ====================

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)
    favorite_genres = models.CharField(max_length=200, blank=True, help_text="User's favorite book genres")

    def __str__(self):
        return str(self.user)

# ==================== CART MODELS ====================

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart ({self.user.username})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return float(sum(item.total_price for item in self.items.all()))

    @property
    def total_discount(self):
        return float(sum(item.total_discount for item in self.items.all()))

    @property
    def final_total(self):
        return self.subtotal - self.total_discount

    @property
    def tax(self):
        """Calculate tax (8% example)"""
        return round(self.final_total * 0.08, 2)

    @property
    def grand_total(self):
        return self.final_total + self.tax

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'book']

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    @property
    def total_price(self):
        return float(self.book.price) * self.quantity

    @property
    def total_discount(self):
        if self.book.discount_price:
            return (float(self.book.price) - float(self.book.discount_price)) * self.quantity
        return 0.0

    @property
    def final_price(self):
        if self.book.discount_price:
            return float(self.book.discount_price) * self.quantity
        return float(self.book.price) * self.quantity

class Category(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_index=True)
    slug = models.SlugField(null=False, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("eco:category-detail", kwargs={
            'slug': self.slug
        })

    @property
    def book_count(self):
        return self.books.count()

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = "Categories"

class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='author_images/', blank=True, null=True)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("eco:author-detail", kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "No image"

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Book(models.Model):
    # Basic Information
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)
    additional_authors = models.CharField(max_length=200, blank=True, help_text="Other authors, separated by commas")
    isbn = models.CharField(max_length=13, blank=True, verbose_name="ISBN")
    isbn13 = models.CharField(max_length=17, blank=True, verbose_name="ISBN-13")
    
    # Categorization
    category = TreeForeignKey(Category, related_name='books', on_delete=models.SET_NULL, null=True, blank=True)
    genre = models.CharField(max_length=20, choices=BOOK_GENRES, blank=True)
    format_type = models.CharField(max_length=10, choices=BOOK_FORMATS, default='PAPERBACK')
    condition = models.CharField(max_length=10, choices=BOOK_CONDITIONS, default='NEW')
    
    # Publishing Information
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, default='English')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

   # NEW FIELD: Featured Book
    featured = models.BooleanField(default=False, help_text="Mark this book as featured on homepage")
    
    # Labels & Status
    label1 = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True)
    label2 = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True)
    label3 = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True)
    
    # Media & Content - UPDATED IMAGE FIELDS
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, help_text="Main book cover image")
    additional_images = models.ImageField(upload_to='book_images/', blank=True, null=True, help_text="Additional book images")
    description = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Short excerpt or first chapter")
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    # Metadata
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Book"
        verbose_name_plural = "Books"
    
    def __str__(self):
        author_name = self.author.name if self.author else 'Unknown Author'
        return f"{self.title} by {author_name}"
    
    def get_absolute_url(self):
        return reverse("eco:product-detail", kwargs={'slug': self.slug})
    
    def get_add_to_cart_url(self):
        return reverse("eco:add-to-cart", kwargs={'slug': self.slug})
    
    def get_remove_from_cart_url(self):
        return reverse("eco:remove-from-cart", kwargs={'slug': self.slug})
    
    def get_remove_from_single_cart_url(self):
        return reverse("eco:remove-single-item-from-cart", kwargs={'slug': self.slug})
    
    def get_add_to_wish_url(self):
        return reverse("eco:add-to-wish", kwargs={'slug': self.slug})
    
    def get_remove_from_wish_url(self):
        return reverse("eco:remove-from-wish", kwargs={'slug': self.slug})
    
    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price
    
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((float(self.price) - float(self.discount_price)) / float(self.price)) * 100)
        return 0
    
    @property
    def final_price(self):
        return self.discount_price if self.is_on_sale else self.price
    
    @property
    def image_preview(self):
        """HTML preview for admin"""
        if self.cover_image:
            return mark_safe(f'<img src="{self.cover_image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "No image"
    
    @property
    def image_url(self):
        """Returns image URL for templates with fallback"""
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return '/static/images/placeholder-book.jpg'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Book.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Update availability based on stock
        self.is_available = self.stock_quantity > 0
        
        super().save(*args, **kwargs)

class BookImage(models.Model):
    """Model for multiple book images"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='book_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.book.title}"
    
    class Meta:
        ordering = ['-is_primary', 'created_at']

class BookReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['book', 'user']
    
    def __str__(self):
        return f"Review for {self.book.title} by {self.user.username}"
    
    @property
    def stars(self):
        return '★' * self.rating + '☆' * (5 - self.rating)

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.book.title}"
    
    class Meta:
        unique_together = ['user', 'book']
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} of {self.book.title}"
    
    def get_total_item_price(self):
        return self.quantity * float(self.book.price)
    
    def get_total_discount_item_price(self):
        if self.book.discount_price:
            return self.quantity * float(self.book.discount_price)
        return self.get_total_item_price()
    
    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        return self.get_total_discount_item_price()
    
    def get_final_price_list(self):
        return self.get_final_price()

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(null=True, blank=True)
    ordered = models.BooleanField(default=False)
    
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Order {self.ref_code} - {self.user.username}"
    
    def get_total(self):
        total = sum(item.get_final_price() for item in self.items.all())
        if self.coupon:
            total -= float(self.coupon.amount)
        return total
    
    def get_total_full(self):
        return self.get_total()

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100, blank=True)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=20, default="00000")
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.street_address}, {self.country}"
    
    class Meta:
        verbose_name_plural = 'Addresses'

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.stripe_charge_id

class Coupon(models.Model):
    code = models.CharField(max_length=15, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(default=timezone.now() + timedelta(days=30))  # 30 days default
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()
    
    def __str__(self):
        return f"Refund {self.pk} for Order {self.order.ref_code}"

# ==================== SIGNALS ====================

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

def create_user_cart(sender, instance, created, *args, **kwargs):
    if created:
        Cart.objects.create(user=instance)

post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
post_save.connect(create_user_cart, sender=settings.AUTH_USER_MODEL)