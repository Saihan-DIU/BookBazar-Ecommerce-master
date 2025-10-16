# eco/context_processors.py
from .models import Order

def cart_count(request):
    """
    Context processor to add cart count to all templates
    """
    cart_count = 0
    if request.user.is_authenticated:
        try:
            # Get the user's active order (ordered=False)
            order_qs = Order.objects.filter(user=request.user, ordered=False)
            if order_qs.exists():
                order = order_qs[0]
                # Count total items in the order
                cart_count = order.items.count()
        except Exception as e:
            # If any error occurs, set cart_count to 0
            cart_count = 0
    return {'cart_count': cart_count}