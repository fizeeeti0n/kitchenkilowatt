import uuid
from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant
from decimal import Decimal
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('PERCENTAGE', 'Percentage Discount (%)'),
        ('FIXED', 'Fixed Amount Discount ($)'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='PERCENTAGE')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)

    def is_valid(self, cart_subtotal=0):
        now = timezone.now()
        if not self.active:
            return False, "This coupon is no longer active."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon is expired or not yet valid."
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        if Decimal(cart_subtotal) < self.min_purchase_amount:
            return False, f"Minimum purchase amount of ${self.min_purchase_amount} required for this coupon."
        return True, "Valid coupon"

    def calculate_discount(self, subtotal):
        subtotal = Decimal(subtotal)
        if self.discount_type == 'PERCENTAGE':
            discount = subtotal * (self.discount_value / Decimal(100))
        else:
            discount = self.discount_value
        return min(discount, subtotal)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'PERCENTAGE' else '$'} off)"

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('STRIPE', 'Stripe Credit/Debit Card'),
        ('CARD_SANDBOX', 'Demo Express Card (Sandbox)'),
        ('COD', 'Cash on Delivery (COD)'),
    )

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    
    shipping_address_text = models.TextField()
    billing_address_text = models.TextField(blank=True)
    shipping_method = models.CharField(max_length=50, default='Standard Delivery ($5.00)')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='STRIPE')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"KK-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.price * Decimal(self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in Order #{self.order.order_number}"
