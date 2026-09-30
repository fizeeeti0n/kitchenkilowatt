from products.models import Category, Wishlist
from cart.models import Cart

def global_store_context(request):
    """
    Context processor to make cart_count, wishlist_count, and main_categories 
    available across all Django templates.
    """
    categories = Category.objects.filter(parent__isnull=True)[:8]
    cart_count = 0
    wishlist_count = 0
    
    # Cart calculation
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.total_items
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_count = wishlist.products.count()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            if cart:
                cart_count = cart.total_items

    return {
        'nav_categories': categories,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'STORE_NAME': 'Kitchen & Kilowatt',
        'STORE_TAGLINE': 'Power your kitchen with high-performance culinary tech.',
    }
