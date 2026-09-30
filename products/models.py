from django.db import models
from django.utils.text import slugify
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class name, e.g. fa-blender")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    short_description = models.CharField(max_length=300, help_text="Catchy 1-line summary")
    description = models.TextField()
    features = models.JSONField(default=list, blank=True, help_text="List of bullet point features")
    specifications = models.JSONField(default=dict, blank=True, help_text="Dict of tech specs e.g. Power, Capacity")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    rating_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.discount_price if self.discount_price and self.discount_price < self.price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.price:
            return int(round((1 - (self.discount_price / self.price)) * 100))
        return 0

    @property
    def total_stock(self):
        # Calculate from associated stock items
        from inventory.models import Stock
        stock_items = Stock.objects.filter(product=self)
        if stock_items.exists():
            return sum(s.quantity for s in stock_items)
        return 0

    @property
    def is_in_stock(self):
        return self.total_stock > 0

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g. Copper Finish / 1500W")
    sku = models.CharField(max_length=60, unique=True)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True, help_text="e.g. {'Color': 'Copper', 'Capacity': '1.7L'}")
    is_active = models.BooleanField(default=True)

    @property
    def price(self):
        return self.price_override if self.price_override else self.product.current_price

    def __str__(self):
        return f"{self.product.name} - {self.name}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', '-is_primary']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

class Banner(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=250, blank=True)
    badge = models.CharField(max_length=50, blank=True, default="NEW ARRIVAL")
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    button_text = models.CharField(max_length=50, default="Shop Now")
    button_link = models.CharField(max_length=200, default="/products/")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title
