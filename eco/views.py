import random
import string
import stripe

from django.shortcuts import render, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, View, FormView,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Book, Order, OrderItem
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
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
    # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
    categories = Category.objects.annotate(
        total_books=Count('books', filter=Q(books__is_available=True))
    )
    
    # Get featured books for the home page
    featured_books = Book.objects.filter(
        featured=True, 
        is_available=True
    ).select_related('author', 'category')[:6]
    
    # Get cart count for the navbar
    cart_count = 0
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, ordered=False).first()
        if order:
            cart_count = order.items.count()
    
    context = {
        'featured_books': featured_books,
        'categories': categories,  # Now includes total_books
        'cart_count': cart_count,
    }
    return render(request, 'eco/base.html', context)

# ==================== BROWSE BOOKS VIEW ====================

def browse_books(request):
    """Browse all books page with search functionality"""
    # Get all available books, ordered by newest first
    queryset = Book.objects.filter(is_available=True).select_related('author', 'category').order_by('-created_at')
    
    # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
    categories = Category.objects.annotate(
        total_books=Count('books', filter=Q(books__is_available=True))
    )
    
    # Pagination - 12 books per page
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get cart count for the navbar
    cart_count = 0
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, ordered=False).first()
        if order:
            cart_count = order.items.count()
    
    context = {
        'queryset': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': categories,  # Now includes total_books
        'cart_count': cart_count,
    }
    return render(request, 'eco/browse_books.html', context)

# ==================== CART FUNCTIONALITY ====================

@login_required
def add_to_cart(request, slug):
    """Add item to cart - UPDATED for home page functionality"""
    book = get_object_or_404(Book, slug=slug)
    
    # Check if book is available
    if not book.is_available:
        messages.warning(request, f"Sorry, {book.title} is out of stock.")
        return redirect("eco:home")
    
    # Get or create order item
    order_item, created = OrderItem.objects.get_or_create(
        book=book,
        user=request.user,
        ordered=False
    )
    
    # Get user's active order
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    
    if order_qs.exists():
        order = order_qs[0]
        # Check if the item is already in the order
        if order.items.filter(book__slug=book.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, f"{book.title} quantity updated in your cart!")
            return redirect("eco:order-summary")
        else:
            order.items.add(order_item)
            messages.success(request, f"{book.title} added to your cart!")
            return redirect("eco:home")
    else:
        # Create new order
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.success(request, f"{book.title} added to your cart!")
        return redirect("eco:home")

def order_summary(request):
    """Cart summary page - UPDATED for function-based view"""
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, ordered=False).first()
        context = {
            'order': order
        }
    else:
        context = {'order': None}
        messages.info(request, "Please login to view your cart.")
        return redirect('login')
    
    return render(request, 'eco/basket.html', context)

# ==================== SEARCH & PRODUCT VIEWS ====================

class SearchView(View):
    def get(self, request, *args, **kwargs):
        try:
            queryset1 = Book.objects.all()
            # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
                'categories': categories,  # Now includes total_books
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        else:
            context['in_wishlist'] = False
            
        return context

class CategoryDetail(DetailView, MultipleObjectMixin):
    model = Category
    template_name = 'eco/category.html'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        object_list = Book.objects.filter(category=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
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
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("eco:order-summary")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the default shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('eco:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip_code')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the default billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('eco:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip_code')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('eco:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('eco:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('eco:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("eco:order-summary")

class Paypal(TemplateView):
    template_name = 'eco/paypal.html'

class PaymentView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
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
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("eco:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    charge = stripe.Charge.create(
                        amount=amount,
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    charge = stripe.Charge.create(
                        amount=amount,
                        currency="usd",
                        source=token
                    )

                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")

# ==================== CART MANAGEMENT ====================

@login_required
def remove_from_cart(request, slug):
    book = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(book__slug=book.slug).exists():
            order_item = OrderItem.objects.filter(
                book=book,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Book was removed from your cart.")
            return redirect("eco:order-summary")
        else:
            messages.info(request, "This book was not in your cart")
            return redirect("eco:product-detail", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("eco:product-detail", slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    book = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(book__slug=book.slug).exists():
            order_item = OrderItem.objects.filter(
                book=book,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, "Book quantity was updated.")
            else:
                order.items.remove(order_item)
                messages.info(request, "Book was removed from your cart.")
            return redirect("eco:order-summary")
        else:
            messages.info(request, "This book was not in your cart")
            return redirect("eco:product-detail", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("eco:product-detail", slug=slug)

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
        return redirect("eco:order-summary")

class AddCouponView(LoginRequiredMixin,View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon applied successfully!")
                return redirect("eco:order-summary")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("eco:order-summary")

# ==================== CONTACT & ACCOUNT ====================

class ContactView(FormView):
    form_class = ContactForm
    success_url = reverse_lazy('eco:contact')
    template_name = 'eco/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
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
            'categories': categories,  # Now includes total_books
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
        # Get categories with book counts - FIXED: Changed annotation name to avoid conflict
        context['categories'] = Category.objects.annotate(
            total_books=Count('books', filter=Q(books__is_available=True))
        )
        context['current_category'] = None
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
            
        return context