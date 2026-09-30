from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomerProfile
from products.models import Wishlist

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_and_wishlist(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.create(user=instance)
        Wishlist.objects.create(user=instance)
