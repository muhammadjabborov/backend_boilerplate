from django.contrib import admin
from .models import UserAPIKey, PnLData


@admin.register(UserAPIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'api_key', 'created_at')
    search_fields = ('user__username', 'api_key')
    list_filter = ('created_at',)


@admin.register(PnLData)
class PnLDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'range_type', 'date')
    search_fields = ('user__username', 'range_type')
    list_filter = ('range_type', 'date')
    readonly_fields = ('data',)  # Make the JSON field read-only in admin

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
