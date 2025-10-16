# eco/urls.py
from django.urls import path
from . import views

app_name = 'eco'

urlpatterns = [
    # ==================== HOME PAGE ====================
    # Homepage - using base.html as template
    path('', views.home, name='home'),
    
    # ==================== PRODUCTS ====================
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('product/<slug:slug>/', views.EcoDetail.as_view(), name='product-detail'),
    
    # ==================== CART & ORDER MANAGEMENT ====================
    path('order-summary/', views.order_summary, name='order-summary'),
    path('add-to-cart/<slug:slug>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug:slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug:slug>/', views.remove_single_item_from_cart, name='remove-single-item-from-cart'),
    
    # ==================== CHECKOUT & PAYMENT ====================
    path('checkout/', views.Checkout.as_view(), name='checkout'),
    path('payment/<str:payment_option>/', views.PaymentView.as_view(), name='payment'),
    path('paypal/', views.Paypal.as_view(), name='paypal'),
    
    # ==================== USER ACCOUNT ====================
    path('account/', views.Accounts.as_view(), name='customer-account'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # ==================== CATEGORIES ====================
    path('categories/', views.EcoIndex.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetail.as_view(), name='category-detail'),
    
    # ==================== WISHLIST ====================
    path('wish-summary/', views.WishSummaryView.as_view(), name='wish-summary'),
    path('add-to-wish/<slug:slug>/', views.add_to_wish, name='add-to-wish'),
    path('remove-from-wish/<slug:slug>/', views.remove_from_wish, name='remove-from-wish'),
    
    # ==================== COUPONS ====================
    path('add-coupon/', views.AddCouponView.as_view(), name='add-coupon'),
    
    # ==================== STATIC PAGES ====================
    path('faq/', views.Faq.as_view(), name='faq'),
    path('text/', views.Text.as_view(), name='text'),
    
    # ==================== SEARCH ====================
    path('search/', views.SearchView.as_view(), name='search'),
    
    # ==================== PRODUCT MANAGEMENT (STAFF ONLY) ====================
    path('add-product/', views.AddProductView.as_view(), name='add-product'),
    path('edit-product/<slug:slug>/', views.EditProductView.as_view(), name='edit-product'),
    path('delete-product/<slug:slug>/', views.DeleteProductView.as_view(), name='delete-product'),
    path('add-category/', views.AddCategoryView.as_view(), name='add-category'),
    
    # ==================== ADVANCED SEARCH ====================
    path('product-search/', views.ProductSearchView.as_view(), name='product-search'),
    path('products/category/<slug:category_slug>/', views.ProductListView.as_view(), name='products-by-category'),
]