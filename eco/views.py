import random
import string
import stripe
import json

from django.shortcuts import render, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, View, FormView,
)
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Book, Order, OrderItem, Cart, CartItem
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.views.generic.list import MultipleObjectMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from itertools import chain
from django.db.models import Count, Q
from django.utils import timezone
from .models import *
from .forms import *

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

# ==================== HOME PAGE VIEW ====================

def home(request):
    """Home page view - renders base.html as home page"""
    # Get categories with book counts
    categories = Category.objects.annotate(
        total_books=Count('books', filter=Q(books__is_available=True))
    )
    
    # Get featured books for the home page
    featured_books = Book.objects.filter(
        featured=True, 
        is_available=True
    ).select_related('author', 'category')[:6]
    
    # Get cart count for the navbar - UPDATED for new Cart system
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
        except Cart.DoesNotExist:
            cart_count = 0
    
    context = {
        'featured_books': featured_books,
        'categories': categories,
        'cart_count': cart_count,
    }
    return render(request, 'eco/base.html', context)

# ==================== BROWSE BOOKS VIEW ====================

def browse_books(request):
    """Browse all books page with search functionality"""
    # Get all available books, ordered by newest first
    queryset = Book.objects.filter(is_available=True).select_related('author', 'category').order_by('-created_at')
    
    # Get categories with book counts
    categories = Category.objects.annotate(
        total_books=Count('books', filter=Q(books__is_available=True))
    )
    
    # Pagination - 12 books per page
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get cart count for the navbar - UPDATED for new Cart system
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
        except Cart.DoesNotExist:
            cart_count = 0
    
    context = {
        'queryset': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': categories,
        'cart_count': cart_count,
    }
    return render(request, 'eco/browse_books.html', context)

# ==================== NEW CART FUNCTIONALITY ====================

@login_required
def cart_view(request):
    """Cart summary page using new Cart model"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('book').all()
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
        }
        return render(request, 'eco/basket.html', context)
    except Cart.DoesNotExist:
        context = {'cart': None, 'cart_items': []}
        return render(request, 'eco/basket.html', context)

@login_required
def add_to_cart(request, slug):
    """Add item to cart using new Cart system"""
    book = get_object_or_404(Book, slug=slug)
    
    # Check if book is available
    if not book.is_available:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Sorry, {book.title} is out of stock."
            })
        messages.warning(request, f"Sorry, {book.title} is out of stock.")
        return redirect("eco:home")
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{book.title} added to your cart!",
            'total_items': cart.total_items
        })
    
    messages.success(request, f"{book.title} added to your cart!")
    return redirect("eco:home")

@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
            elif action == 'decrease' and cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            elif action == 'remove':
                cart_item.delete()
            
            cart = Cart.objects.get(user=request.user)
            
            return JsonResponse({
                'success': True,
                'item_quantity': cart_item.quantity if action != 'remove' else 0,
                'item_total': float(cart_item.final_price) if action != 'remove' else 0,
                'subtotal': float(cart.subtotal),
                'total_discount': float(cart.total_discount),
                'final_total': float(cart.final_total),
                'total_items': cart.total_items
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False})

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        book_title = cart_item.book.title
        cart_item.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart = Cart.objects.get(user=request.user)
            return JsonResponse({
                'success': True,
                'message': f"{book_title} removed from cart",
                'total_items': cart.total_items,
                'subtotal': float(cart.subtotal),
                'total_discount': float(cart.total_discount),
                'final_total': float(cart.final_total)
            })
        
        messages.info(request, f"{book_title} removed from cart")
        return redirect("eco:cart")
    
    return redirect("eco:cart")

# ==================== LEGACY CART FUNCTIONALITY (for backward compatibility) ====================

@login_required
def order_summary(request):
    """Legacy cart summary - redirects to new cart system"""
    return redirect("eco:cart")

@login_required
def remove_from_cart_legacy(request, slug):
    """Legacy remove from cart - redirects to new system"""
    book = get_object_or_404(Book, slug=slug)
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, book=book)
        cart_item.delete()
        messages.info(request, f"{book.title} removed from cart")
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        messages.info(request, "Item not found in cart")
    
    return redirect("eco:cart")

@login_required
def remove_single_item_from_cart(request, slug):
    """Legacy remove single item - redirects to new system"""
    book = get_object_or_404(Book, slug=slug)
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, book=book)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.info(request, f"{book.title} quantity updated")
        else:
            cart_item.delete()
            messages.info(request, f"{book.title} removed from cart")
            
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        messages.info(request, "Item not found in cart")
    
    return redirect("eco:cart")



# ==================== SEARCH & PRODUCT VIEWS ====================

class SearchView(View):
    def get(self, request, *args, **kwargs):
        try:
            queryset1 = Book.objects.all()
            categories = Category.objects.annotate(
                total_books=Count('books', filter=Q(books__is_available=True))
            )
            query = request.GET.get('q')
            if query:
                queryset1 = queryset1.filter(
                    Q(title__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(price__icontains=query) |
                    Q(author__icontains=query) |
                    Q(isbn__icontains=query)
                ).distinct()
                queryset = list(
                    sorted(
                        chain(queryset1),
                        key=lambda objects: objects.pk
                    ))
            else:
                queryset = queryset1
                
            context = {
                'queryset': queryset,
                'categories': categories,
                'query': query,
            }
            return render(request, 'eco/results.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "Search based on title, author, ISBN, or price")
            return redirect("eco:home")

class EcoIndex(ListView):
    model = Book
    template_name = 'eco/category.html'
    context_object_name = 'queryset'
    paginate_by = 6

    def get_queryset(self):
        return Book.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        return context

class EcoDetail(DetailView):
    model = Book
    template_name = 'eco/detail.html'   
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['related_items'] = Book.objects.filter(category=self.object.category).exclude(pk=self.object.pk)[:3]
        
        # Check if book is in user's wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(
                user=self.request.user, 
                book=self.object
            ).exists()
            
            # Check if book is in user's cart (new system)
            try:
                cart = Cart.objects.get(user=self.request.user)
                context['in_cart'] = CartItem.objects.filter(
                    cart=cart, 
                    book=self.object
                ).exists()
            except Cart.DoesNotExist:
                context['in_cart'] = False
        else:
            context['in_wishlist'] = False
            context['in_cart'] = False
            
        return context

class CategoryDetail(DetailView, MultipleObjectMixin):
    model = Category
    template_name = 'eco/category.html'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        object_list = Book.objects.filter(category=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        return context

# ==================== CHECKOUT & PAYMENT ====================

class Login(TemplateView):
    template_name = 'eco/register.html'

class CheckoutView(LoginRequiredMixin, TemplateView):
    model = Order
    template_name = 'eco/checkout.html'
    context_object_name = 'queryset'

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

class Checkout(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            # Using new Cart system for checkout
            cart = Cart.objects.get(user=self.request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                messages.info(self.request, "Your cart is empty")
                return redirect("eco:cart")
                
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'cart': cart,
                'cart_items': cart_items,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
                
            return render(self.request, "eco/checkout.html", context)
        except Cart.DoesNotExist:
            messages.info(self.request, "Your cart is empty")
            return redirect("eco:cart")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            cart = Cart.objects.get(user=self.request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                messages.info(self.request, "Your cart is empty")
                return redirect("eco:cart")
                
            if form.is_valid():
                # Process shipping address
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('eco:checkout')
                else:
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip_code')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip_code=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required shipping address fields")
                        return redirect('eco:checkout')

                # Process billing address
                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                elif use_default_billing:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                    else:
                        messages.info(self.request, "No default billing address available")
                        return redirect('eco:checkout')
                else:
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip_code')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip_code=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required billing address fields")
                        return redirect('eco:checkout')

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('eco:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('eco:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect('eco:checkout')
                    
        except Cart.DoesNotExist:
            messages.warning(self.request, "Your cart is empty")
            return redirect("eco:cart")

class Paypal(TemplateView):
    template_name = 'eco/paypal.html'

class PaymentView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            cart = Cart.objects.get(user=self.request.user)
            if not cart.items.exists():
                messages.warning(self.request, "Your cart is empty")
                return redirect("eco:cart")
                
            # For now, we'll use the existing Order system for payments
            # You might want to create an Order from the Cart here
            order_qs = Order.objects.filter(user=self.request.user, ordered=False)
            if order_qs.exists():
                order = order_qs[0]
            else:
                # Create order from cart (simplified - you might want to improve this)
                order = Order.objects.create(user=self.request.user)
                # Convert cart items to order items
                for cart_item in cart.items.all():
                    order_item, created = OrderItem.objects.get_or_create(
                        book=cart_item.book,
                        user=self.request.user,
                        ordered=False,
                        defaults={'quantity': cart_item.quantity}
                    )
                    if not created:
                        order_item.quantity = cart_item.quantity
                        order_item.save()
                    order.items.add(order_item)
            
            if order.billing_address:
                context = {
                    'order': order,
                    'DISPLAY_COUPON_FORM': False,
                    'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
                }
                userprofile = self.request.user.userprofile
                if userprofile.one_click_purchasing:
                    cards = stripe.Customer.list_sources(
                        userprofile.stripe_customer_id,
                        limit=3,
                        object='card'
                    )
                    card_list = cards['data']
                    if len(card_list) > 0:
                        context.update({
                            'card': card_list[0]
                        })
                return render(self.request, "eco/payment.html", context)
            else:
                messages.warning(self.request, "You have not added a billing address")
                return redirect("eco:checkout")
        except Cart.DoesNotExist:
            messages.warning(self.request, "Your cart is empty")
            return redirect("eco:cart")

    def post(self, *args, **kwargs):
        # Payment processing logic remains similar to existing
        # You'll need to adapt this to work with the new cart system
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        
        if form.is_valid():
            # Existing payment processing logic...
            # After successful payment, clear the cart
            try:
                cart = Cart.objects.get(user=self.request.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
                
            # Rest of payment logic...
            pass

# ==================== WISHLIST ====================

class WishSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            wish = Wishlist.objects.filter(user=self.request.user)
            context = {
                'object': wish
            }
            return render(self.request, 'eco/customer-wishlist.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have a wishlist")
            return redirect("eco:home")

@login_required
def add_to_wish(request, slug):
    book = get_object_or_404(Book, slug=slug)
    wish_item, created = Wishlist.objects.get_or_create(
        book=book,
        user=request.user
    )
    
    if created:
        messages.info(request, "Book was added to your wishlist")
    else:
        messages.warning(request, "Book was already in your wishlist")
    return redirect('eco:product-detail', slug=book.slug)

@login_required
def remove_from_wish(request, slug):
    book = get_object_or_404(Book, slug=slug)
    wish_qs = Wishlist.objects.filter(
        book=book,
        user=request.user
    )
    if wish_qs.exists():
        wish = wish_qs[0]
        wish.delete()
        messages.info(request, "Book was removed from your wishlist.")
        return redirect("eco:wish-summary")
    else:
         return redirect("eco:wish-summary")

# ==================== COUPONS ====================


@login_required
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("eco:cart")

class AddCouponView(LoginRequiredMixin,View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                # For now, apply to order - you might want to adapt this for cart
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon applied successfully!")
                return redirect("eco:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("eco:cart")

# MOVE THIS FUNCTION OUTSIDE THE CLASS - FIX THE INDENTATION
@require_POST
def apply_promo_code(request):
    try:
        data = json.loads(request.body)
        promo_code = data.get('promo_code', '').strip().upper()
        
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to apply promo codes.'
            })
        
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No cart found. Please add items to your cart first.'
            })
        
        try:
            coupon = Coupon.objects.get(code=promo_code, active=True)
            
            # Check if coupon is valid (within date range)
            now = timezone.now()
            if not (coupon.valid_from <= now <= coupon.valid_to):
                return JsonResponse({
                    'success': False,
                    'message': 'This promo code has expired.'
                })
            
            # Store the applied coupon in session
            request.session['applied_coupon'] = {
                'code': coupon.code,
                'amount': float(coupon.amount),
                'id': coupon.id
            }
            
            # Calculate the discount using the cart's current totals
            discount_amount = float(coupon.amount)
            
            # Use the cart's own calculation methods
            # The cart's final_total already excludes tax
            new_final_total = max(0, cart.final_total - discount_amount)
            
            return JsonResponse({
                'success': True,
                'message': f'Promo code applied! ${discount_amount:.2f} discount added.',
                'discount_amount': discount_amount,
                'cart_data': {
                    'subtotal': float(cart.subtotal),
                    'final_total': float(new_final_total),
                    'total_items': cart.total_items,
                    'total_discount': float(cart.total_discount) + discount_amount,
                    'grand_total': float(new_final_total)  # No tax added
                }
            })
            
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired promo code.'
            })
            
    except Exception as e:
        print(f"Error applying promo code: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while applying the promo code.'
        })

# ==================== CONTACT & ACCOUNT ====================

class ContactView(FormView):
    form_class = ContactForm
    success_url = reverse_lazy('eco:contact')
    template_name = 'eco/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        return context

    def form_valid(self, form):
        name = form.cleaned_data['name']
        from_email = form.cleaned_data['email']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']  
        try:
            full_message = f"Name: {name}\nEmail: {from_email}\n\nMessage:\n{message}"
            send_mail(
                subject=f"BookBazar Contact: {subject}",
                message=full_message,
                from_email=from_email,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(self.request, "Your message has been sent successfully!")
        except BadHeaderError:
            messages.error(self.request, "There was an error sending your message.")
            return HttpResponse('Invalid header found.')
        except Exception as e:
            messages.error(self.request, "There was an error sending your message.")
        return super().form_valid(form)

class AccountUpdate(UpdateView):
    pass

class Accounts(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'eco/customer-account.html'
    success_url = reverse_lazy('eco:wish-summary')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['address'] = Address.objects.filter(user=self.request.user)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Address added successfully!")
        return response

class Faq(TemplateView):
    template_name = "eco/faq.html"

class Text(TemplateView):
    template_name = "eco/text.html"

# ==================== PRODUCT MANAGEMENT VIEWS ====================

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class AddProductView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = ProductForm
    template_name = 'eco/add_product.html'
    success_url = reverse_lazy('eco:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['title'] = 'Add New Book'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Book added successfully!')
        return super().form_valid(form)

class EditProductView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = ProductForm
    template_name = 'eco/add_product.html'
    success_url = reverse_lazy('eco:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['title'] = 'Edit Book'
        context['editing'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Book updated successfully!')
        return super().form_valid(form)

class DeleteProductView(StaffRequiredMixin, View):
    def post(self, request, slug):
        product = get_object_or_404(Book, slug=slug)
        product_title = product.title
        product.delete()
        messages.success(request, f'Book "{product_title}" deleted successfully!')
        return redirect('eco:home')

class AddCategoryView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'eco/add_category.html'
    success_url = reverse_lazy('eco:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['title'] = 'Add New Category'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Category added successfully!')
        return super().form_valid(form)

class ProductSearchView(View):
    def get(self, request, *args, **kwargs):
        form = ProductSearchForm(request.GET)
        products = Book.objects.all()
        categories = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )

        if form.is_valid():
            query = form.cleaned_data.get('query')
            category_filter = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')

            if query:
                products = products.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(author__icontains=query) |
                    Q(isbn__icontains=query) |
                    Q(category__name__icontains=query)
                )

            if category_filter:
                products = products.filter(category=category_filter)

            if min_price:
                products = products.filter(price__gte=min_price)

            if max_price:
                products = products.filter(price__lte=max_price)

        context = {
            'form': form,
            'products': products,
            'categories': categories,
            'query': request.GET.get('query', ''),
        }
        return render(request, 'eco/product_search.html', context)

class ProductListView(ListView):
    model = Book
    template_name = 'eco/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.kwargs.get('category_slug')
        
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['current_category'] = None
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
            
        return context