from django.shortcuts import render, get_object_or_404
from .models import Product, Banner, Category

def home_view(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]
    banners = Banner.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'banners': banners
    })

def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    cat_slug = request.GET.get('category')
    if cat_slug:
        products = products.filter(category__slug=cat_slug)
        
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': cat_slug
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/product_detail.html', {'product': product})
