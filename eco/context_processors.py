# eco/context_processors.py
from .models import Order, Cart

def cart_count(request):
    """
    Context processor to add cart count to all templates
    Uses new Cart system if available, falls back to legacy Order system
    """
    cart_count = 0
    if request.user.is_authenticated:
        try:
            # Try new Cart system first
            try:
                cart = Cart.objects.get(user=request.user)
                cart_count = cart.total_items
            except Cart.DoesNotExist:
                # Fall back to legacy Order system
                order_qs = Order.objects.filter(user=request.user, ordered=False)
                if order_qs.exists():
                    order = order_qs[0]
                    cart_count = order.items.count()
        except Exception as e:
            # If any error occurs, set cart_count to 0
            cart_count = 0
    return {'cart_count': cart_count}

def cart_context(request):
    """
    Extended context processor that provides full cart data
    """
    context = {
        'cart_count': 0,
        'cart': None,
        'cart_items': []
    }
    
    if request.user.is_authenticated:
        try:
            # Try new Cart system first
            try:
                cart = Cart.objects.get(user=request.user)
                cart_items = cart.items.select_related('book').all()
                
                context.update({
                    'cart_count': cart.total_items,
                    'cart': cart,
                    'cart_items': cart_items,
                    'cart_subtotal': cart.subtotal,
                    'cart_total_discount': cart.total_discount,
                    'cart_final_total': cart.final_total,
                })
            except Cart.DoesNotExist:
                # Fall back to legacy Order system
                order_qs = Order.objects.filter(user=request.user, ordered=False)
                if order_qs.exists():
                    order = order_qs[0]
                    order_items = order.items.all()
                    
                    context.update({
                        'cart_count': order.items.count(),
                        'cart': order,  # Using order as cart for compatibility
                        'cart_items': order_items,
                    })
                    
        except Exception as e:
            # If any error occurs, use default values
            pass
            
    return context

# Optional: Simple version for just the count
def simple_cart_count(request):
    """
    Lightweight context processor for just the cart count
    """
    if request.user.is_authenticated:
        try:
            # Try new Cart system
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                return {'cart_count': cart.total_items}
            
            # Fall back to legacy Order system
            order = Order.objects.filter(user=request.user, ordered=False).first()
            if order:
                return {'cart_count': order.items.count()}
                
        except Exception:
            pass
            
    return {'cart_count': 0}