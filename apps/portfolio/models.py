from django.db import models
from django.contrib.auth.models import User

from apps.common.models import BaseModel


class UserAPIKey(BaseModel):
    """
    Model to store API keys for users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_key")
    api_key = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s API Key"

    class Meta:
        verbose_name = "User API Key"
        verbose_name_plural = "User API Keys"


class PnLData(BaseModel):
    """
    Model to store PnL data in a single JSON field.
    """
    RANGE_CHOICES = [
        ('7d', '7 Days'),
        ('30d', '30 Days'),
        ('custom', 'Custom'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pnl_data")
    date = models.DateField(auto_now_add=True)
    range_type = models.CharField(max_length=10, choices=RANGE_CHOICES, default='7d')
    data = models.JSONField()

    def __str__(self):
        return f"{self.user.username} - {self.range_type} - {self.date}"

    class Meta:
        verbose_name = "PnL Data"
        verbose_name_plural = "PnL Data"
