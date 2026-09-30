from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import Order
from inventory.models import Stock, StockLog

# Store previous status in memory before save to detect status transitions
_order_previous_status = {}

@receiver(pre_save, sender=Order)
def track_order_status_before_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            _order_previous_status[instance.pk] = old_order.status
        except Order.DoesNotExist:
            _order_previous_status[instance.pk] = None

@receiver(post_save, sender=Order)
def manage_order_stock_levels(sender, instance, created, **kwargs):
    prev_status = _order_previous_status.pop(instance.pk, None)
    
    with transaction.atomic():
        # Case 1: Order is newly created (and not cancelled)
        if created and instance.status != 'CANCELLED':
            for item in instance.items.all():
                _decrement_stock_for_item(instance, item)
                
        # Case 2: Status changed to CANCELLED from a non-cancelled state
        elif prev_status and prev_status != 'CANCELLED' and instance.status == 'CANCELLED':
            for item in instance.items.all():
                _restore_stock_for_item(instance, item)

        # Case 3: Status changed from CANCELLED back to active status
        elif prev_status == 'CANCELLED' and instance.status != 'CANCELLED':
            for item in instance.items.all():
                _decrement_stock_for_item(instance, item)

def _decrement_stock_for_item(order, item):
    if not item.product:
        return
    stock, _ = Stock.objects.get_or_create(
        product=item.product,
        variant=item.variant,
        defaults={'quantity': 50}
    )
    stock.quantity -= item.quantity
    stock.save()
    
    StockLog.objects.create(
        product=item.product,
        variant=item.variant,
        change_quantity=-item.quantity,
        resulting_quantity=stock.quantity,
        reason='ORDER_PLACED',
        notes=f"Automatic deduction for Order #{order.order_number}",
        created_by=order.user
    )

def _restore_stock_for_item(order, item):
    if not item.product:
        return
    stock, _ = Stock.objects.get_or_create(
        product=item.product,
        variant=item.variant,
        defaults={'quantity': 50}
    )
    stock.quantity += item.quantity
    stock.save()
    
    StockLog.objects.create(
        product=item.product,
        variant=item.variant,
        change_quantity=item.quantity,
        resulting_quantity=stock.quantity,
        reason='ORDER_CANCELLED',
        notes=f"Automatic restoration for cancelled Order #{order.order_number}",
        created_by=order.user
    )
