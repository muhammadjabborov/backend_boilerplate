import datetime
from django_filters import rest_framework as filters
from .models import PnLData
from rest_framework.exceptions import ValidationError
from .tasks import fetch_custom_pnl_data


class PnLDataFilter(filters.FilterSet):
    range_type = filters.CharFilter(method="filter_by_range_type")
    custom_start = filters.DateFilter()
    custom_end = filters.DateFilter()

    class Meta:
        model = PnLData
        fields = ["range_type", "custom_start", "custom_end"]

    def filter_by_range_type(self, queryset, name, value):
        """
        Custom filter to handle '7d', '30d', and 'custom' ranges.
        """
        user = self.request.user
        today = datetime.date.today()

        if value == "7d":
            return queryset.filter(user=user, range_type="7d")

        elif value == "30d":
            return queryset.filter(user=user, range_type="30d")

        elif value == "custom":
            custom_start = self.data.get("custom_start")
            custom_end = self.data.get("custom_end")

            if not custom_start or not custom_end:
                raise ValidationError("Custom range requires start and end dates.")

            try:
                start_date = datetime.datetime.strptime(custom_start, "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(custom_end, "%Y-%m-%d").date()

                if start_date > end_date:
                    raise ValidationError("Start date must be before end date.")

                # Trigger Celery task for custom data calculation
                fetch_custom_pnl_data.delay(user.id, custom_start, custom_end)

                raise ValidationError(
                    {"status": "processing", "message": "Custom range data is being calculated."}
                )
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        else:
            raise ValidationError("Invalid range_type. Use '7d', '30d', or 'custom'.")
