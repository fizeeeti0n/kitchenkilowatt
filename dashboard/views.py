from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta

from products.models import Product, Category
from orders.models import Order, OrderItem
from inventory.models import Stock
from accounts.models import User

@staff_member_required(login_url='/accounts/login/')
def dashboard_home(request):
    """Main admin dashboard with sales, inventory, and order insights."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Order stats
    total_orders = Order.objects.count()
    orders_this_month = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    processing_orders = Order.objects.filter(status='PROCESSING').count()

    # Revenue
    total_revenue = Order.objects.filter(
        payment_status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    monthly_revenue = Order.objects.filter(
        payment_status='PAID', created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Products & Inventory
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_items = Stock.objects.filter(
        quantity__gt=0, quantity__lte=F('low_stock_threshold')
    )
    out_of_stock_items = Stock.objects.filter(quantity__lte=0)

    # Inventory table: product | units sold | units remaining | alert
    inventory_table = []
    for stock in Stock.objects.select_related('product', 'variant').order_by('quantity'):
        product = stock.product
        variant = stock.variant
        label = product.name
        if variant:
            label += f" ({variant.name})"

        units_sold = OrderItem.objects.filter(
            product=product, variant=variant
        ).aggregate(total=Sum('quantity'))['total'] or 0

        alert = ''
        if stock.quantity <= 0:
            alert = 'OUT OF STOCK'
        elif stock.quantity <= stock.low_stock_threshold:
            alert = 'LOW STOCK'

        inventory_table.append({
            'name': label,
            'sku': variant.sku if variant else product.sku,
            'units_sold': units_sold,
            'units_remaining': stock.quantity,
            'alert': alert,
        })

    # Best sellers (by quantity ordered)
    best_sellers = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]

    # Customer count
    total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()

    context = {
        'total_orders': total_orders,
        'orders_this_month': orders_this_month,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_products': total_products,
        'low_stock_count': low_stock_items.count(),
        'out_of_stock_count': out_of_stock_items.count(),
        'inventory_table': inventory_table,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'total_customers': total_customers,
    }
    return render(request, 'dashboard/home.html', context)

@staff_member_required(login_url='/accounts/login/')
def dashboard_orders(request):
    """Order management page."""
    orders = Order.objects.order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/orders.html', {'orders': orders, 'current_status': status_filter})

@staff_member_required(login_url='/accounts/login/')
def dashboard_products(request):
    """Product management page."""
    products = Product.objects.select_related('category', 'brand').prefetch_related('stock_records').order_by('-created_at')
    
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    
    return render(request, 'dashboard/products.html', {
        'products': products,
        'total_products': total_products,
        'active_products': active_products,
    })

@staff_member_required(login_url='/accounts/login/')
def dashboard_customers(request):
    """Customer list page."""
    customers = User.objects.filter(is_staff=False, is_superuser=False).annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total_amount', filter=Q(orders__payment_status='PAID'))
    ).order_by('-date_joined')
    
    total_customers = customers.count()
    active_customers = customers.filter(is_active=True).count()
    
    return render(request, 'dashboard/customers.html', {
        'customers': customers,
        'total_customers': total_customers,
        'active_customers': active_customers,
    })
