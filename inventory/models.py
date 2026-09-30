from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_records')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_records')
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    reorder_quantity = models.PositiveIntegerField(default=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'variant')

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold and self.quantity > 0

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    def __str__(self):
        v_name = f" ({self.variant.name})" if self.variant else ""
        return f"{self.product.name}{v_name}: {self.quantity} units"

class StockLog(models.Model):
    REASON_CHOICES = (
        ('INITIAL', 'Initial Stock Setup'),
        ('MANUAL_RESTOCK', 'Manual Restock Entry'),
        ('ORDER_PLACED', 'Order Placed (Deduction)'),
        ('ORDER_CANCELLED', 'Order Cancelled (Restoration)'),
        ('DAMAGED', 'Damaged Inventory Write-off'),
        ('RETURNED', 'Customer Return Restock'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_logs')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_logs')
    change_quantity = models.IntegerField(help_text="Positive for addition, negative for deduction")
    resulting_quantity = models.IntegerField()
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        v_name = f" ({self.variant.name})" if self.variant else ""
        sign = "+" if self.change_quantity > 0 else ""
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.product.name}{v_name}: {sign}{self.change_quantity} ({self.get_reason_display()})"
