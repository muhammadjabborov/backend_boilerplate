from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserAPIKey
from .tasks import update_pnl_data


@receiver(post_save, sender=UserAPIKey)
def initialize_pnl_data(sender, instance, created, **kwargs):
    """
    Signal triggered when an APIKey is created. Automatically calculates
    and saves 7-day and 30-day PnL data for the associated user.
    """
    if created:
        update_pnl_data.delay(instance.user.id, "7d")
        update_pnl_data.delay(instance.user.id, "30d")
