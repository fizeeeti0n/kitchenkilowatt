from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from cart.views import get_or_create_cart
from .models import Order, OrderItem

def checkout_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    
    if not items:
        return redirect('cart:detail')
        
    subtotal = cart.subtotal
    shipping_cost = 0.00  # Free shipping
    total = subtotal

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', request.user.username if request.user.is_authenticated else 'Customer')
        customer_email = request.POST.get('customer_email', request.user.email if request.user.is_authenticated else 'customer@example.com')
        customer_phone = request.POST.get('customer_phone', '')
        street_address = request.POST.get('street_address', '')
        city = request.POST.get('city', '')
        postal_code = request.POST.get('postal_code', '')
        country = request.POST.get('country', 'United States')

        full_address = f"{street_address}, {city} {postal_code}, {country}".strip(', ')

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address_text=full_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_amount=total,
            status='PENDING',
            payment_status='UNPAID',
            payment_method='STRIPE'
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                product_name=item.product.name,
                variant_name=item.variant.name if item.variant else '',
                price=item.unit_price,
                quantity=item.quantity
            )

        cart.clear()

        return redirect('orders:payment', order_id=order.id)

    context = {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)

def payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'STRIPE')
        card_number = request.POST.get('card_number', '').replace(' ', '')
        
        order.payment_method = payment_method
        
        if payment_method == 'COD':
            order.payment_status = 'UNPAID'
            order.status = 'PROCESSING'
            order.notes = 'Payment Method: Cash on Delivery (COD)'
        else:
            order.payment_status = 'PAID'
            order.status = 'PROCESSING'
            last4 = card_number[-4:] if len(card_number) >= 4 else "4242"
            order.notes = f"Paid via {payment_method} (Card ending in {last4})"

        order.save()
        return render(request, 'orders/order_success.html', {'order': order})

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'orders/payment.html', context)
