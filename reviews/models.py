from django.db import models
from django.conf import settings
from products.models import Product

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=150)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate rating average for product
        approved_reviews = self.product.reviews.filter(is_approved=True)
        count = approved_reviews.count()
        if count > 0:
            avg = sum(r.rating for r in approved_reviews) / count
            self.product.rating_average = round(avg, 2)
            self.product.rating_count = count
            self.product.save(update_fields=['rating_average', 'rating_count'])

    def __str__(self):
        return f"{self.rating}★ Review for {self.product.name} by {self.user.username}"
