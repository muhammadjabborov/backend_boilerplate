from celery import shared_task
from .models import PnLData
from django.contrib.auth.models import User
import logging

from .utils import PnLDashboardService

logger = logging.getLogger(__name__)


@shared_task
def fetch_custom_pnl_data(user_id, custom_start, custom_end):
    """
    Fetch and save custom PnL data for a user.
    """
    user = User.objects.get(id=user_id)
    api_key = user.api_key.api_key
    api_secret = user.api_key.secret_key

    service = PnLDashboardService(api_key, api_secret)

    pnl_data = service.calculate_pnl(date_range="custom", custom_start=custom_start, custom_end=custom_end)

    PnLData.objects.update_or_create(
        user=user,
        range_type="custom",
        defaults={"data": pnl_data}
    )
    return pnl_data


@shared_task
def update_pnl_data(user_id, range_type):
    try:
        user = User.objects.get(id=user_id)
        api_key = user.api_key.api_key
        api_secret = user.api_key.secret_key

        service = PnLDashboardService(api_key, api_secret)

        pnl_data = service.calculate_pnl(date_range=range_type)

        PnLData.objects.update_or_create(
            user=user,
            range_type=range_type,
            defaults={"data": pnl_data}
        )
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Failed to update PnL data for user {user_id}: {str(e)}")
        raise


@shared_task
def update_estimated_balance():
    """
    Fetch and update the estimated balance for all users every 30 minutes.
    """
    users = User.objects.all()

    for user in users:
        api_key = user.api_key.api_key
        api_secret = user.api_key.secret_key

        service = PnLDashboardService(api_key, api_secret)

        total_balance, _ = service.get_current_balance()

        PnLData.objects.update_or_create(
            user=user,
            defaults={"data": {"estimated_balance": total_balance}}
        )
