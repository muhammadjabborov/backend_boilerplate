from rest_framework.response import Response
from collections import defaultdict
from rest_framework.generics import ListAPIView
from .models import PnLData
from rest_framework.exceptions import ValidationError
from django.db.models import F


class MainDashboardView(ListAPIView):
    """
    API view to fetch aggregated PnL data for all users.
    """
    queryset = PnLData.objects.all()

    def list(self, request, *args, **kwargs):
        range_type = request.query_params.get("range_type", "7d")

        if range_type not in ["7d", "30d"]:
            raise ValidationError("Invalid range_type. Use '7d', '30d'.")

        queryset = self.filter_queryset(self.get_queryset().filter(range_type=range_type))

        if not queryset.exists():
            return Response(
                {"status": "error", "message": f"No data available for the selected range: {range_type}"}
            )

        aggregated_data = self.aggregate_pnl_data(queryset)
        return Response({"status": "success", "data": aggregated_data})

    def aggregate_pnl_data(self, queryset):
        """
        Aggregate PnL data across all users.
        """
        aggregated_data = {
            "estimated_balance": 0,
            "estimated_balance_in_btc": 0,
            "today_pnl": {"usdt": 0, "percentage": 0},
            "pnl_7_days": {"usdt": 0, "percentage": 0},
            "pnl_30_days": {"usdt": 0, "percentage": 0},
            "daily_pnl_chart": {"dates": [], "daily_pnl": []},
            "chart_data": {"dates": [], "cumulative_pnl": [], "net_worth": []},
            "profits": 0,
            "profits_chart_data": {
                "dates": [],
                "daily_profits": [],
                "cumulative_profits": [],
            },
            "asset_allocation": [],
        }

        asset_allocation = defaultdict(lambda: {"value_usd": 0, "percentage": 0})
        daily_pnl_sums = defaultdict(float)
        cumulative_pnl_sums = defaultdict(float)
        net_worth_sums = defaultdict(float)
        daily_profits_sums = defaultdict(float)
        cumulative_profits_sums = defaultdict(float)
        date_set = set()

        for pnl in queryset:
            data = pnl.data
            aggregated_data["estimated_balance"] += data.get("estimated_balance", 0)
            aggregated_data["profits"] += data.get("profits", 0)

            today_pnl = data.get("today_pnl", {})
            aggregated_data["today_pnl"]["usdt"] += today_pnl.get("usdt", 0)
            aggregated_data["today_pnl"]["percentage"] += today_pnl.get("percentage", 0)

            pnl_7_days = data.get("pnl_7_days", {})
            aggregated_data["pnl_7_days"]["usdt"] += pnl_7_days.get("usdt", 0)
            aggregated_data["pnl_7_days"]["percentage"] += pnl_7_days.get("percentage", 0)

            pnl_30_days = data.get("pnl_30_days", {})
            aggregated_data["pnl_30_days"]["usdt"] += pnl_30_days.get("usdt", 0)
            aggregated_data["pnl_30_days"]["percentage"] += pnl_30_days.get("percentage", 0)

            aggregated_data["estimated_balance_in_btc"] += data.get("estimated_balance_in_btc", 0)

            daily_pnl_chart = data.get("daily_pnl_chart", {})
            dates = daily_pnl_chart.get("dates", [])
            daily_pnl = daily_pnl_chart.get("daily_pnl", [])
            for i, date in enumerate(dates):
                daily_pnl_sums[date] += daily_pnl[i]
                date_set.add(date)

            chart_data = data.get("chart_data", {})
            cumulative_pnl = chart_data.get("cumulative_pnl", [])
            net_worth = chart_data.get("net_worth", [])
            for i, date in enumerate(dates):
                cumulative_pnl_sums[date] += cumulative_pnl[i]
                net_worth_sums[date] += net_worth[i]

            profits_chart_data = data.get("profits_chart_data", {})
            daily_profits = profits_chart_data.get("daily_profits", [])
            cumulative_profits = profits_chart_data.get("cumulative_profits", [])
            for i, date in enumerate(dates):
                daily_profits_sums[date] += daily_profits[i]
                cumulative_profits_sums[date] += cumulative_profits[i]

            for asset in data.get("asset_allocation", []):
                asset_name = asset["asset"]
                asset_allocation[asset_name]["value_usd"] += asset["value_usd"]
                asset_allocation[asset_name]["percentage"] += asset["percentage"]

        sorted_dates = sorted(date_set)
        aggregated_data["daily_pnl_chart"]["dates"] = sorted_dates
        aggregated_data["daily_pnl_chart"]["daily_pnl"] = [
            daily_pnl_sums[date] for date in sorted_dates
        ]
        aggregated_data["chart_data"]["dates"] = sorted_dates
        aggregated_data["chart_data"]["cumulative_pnl"] = [
            cumulative_pnl_sums[date] for date in sorted_dates
        ]
        aggregated_data["chart_data"]["net_worth"] = [
            net_worth_sums[date] for date in sorted_dates
        ]
        aggregated_data["profits_chart_data"]["dates"] = sorted_dates
        aggregated_data["profits_chart_data"]["daily_profits"] = [
            daily_profits_sums[date] for date in sorted_dates
        ]
        aggregated_data["profits_chart_data"]["cumulative_profits"] = [
            cumulative_profits_sums[date] for date in sorted_dates
        ]
        aggregated_data["asset_allocation"] = [
            {"asset": asset, "value_usd": data["value_usd"], "percentage": data["percentage"]}
            for asset, data in asset_allocation.items()
        ]

        return aggregated_data


class MainDashboardUserBalanceView(ListAPIView):
    """
    API view to fetch balance data for all users for a donut chart visualization
    based on the last 30-day data range.
    """

    def list(self, request, *args, **kwargs):
        user_balances = (
            PnLData.objects.filter(range_type="30d")
            .annotate(
                estimated_balance=F("data__estimated_balance")
            )
            .values("user__id", "user__username", "user__first_name", "user__last_name", "estimated_balance")
        )

        if not user_balances:
            return Response(
                {"status": "error", "message": "No balance data available for any user for the last 30 days."},
                status=404,
            )

        total_balance = sum(
            [float(user["estimated_balance"] or 0) for user in user_balances]
        )
        chart_data = []
        for user in user_balances:
            username = user["user__username"]
            full_name = f"{user['user__first_name']} {user['user__last_name']}".strip()
            balance = float(user["estimated_balance"] or 0)  # Replace None with 0
            percentage = (balance / total_balance) * 100 if total_balance > 0 else 0

            chart_data.append(
                {
                    "id": user["user__id"],
                    "username": username,
                    "full_name": full_name,
                    "estimated_balance": balance,
                    "percentage": percentage,
                }
            )

        return Response(
            {
                "status": "success",
                "total_balance": total_balance,
                "chart_data": chart_data,
            }
        )


class UserDashboardView(ListAPIView):
    """
    API view to fetch aggregated PnL data for a single user.
    """
    queryset = PnLData.objects.all()

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get("pk")
        range_type = request.query_params.get("range_type", "7d")

        if not user_id:
            raise ValidationError("user_id is required.")

        if range_type not in ["7d", "30d"]:
            raise ValidationError("Invalid range_type. Use '7d' or '30d'.")

        queryset = self.filter_queryset(
            self.get_queryset().filter(user_id=user_id, range_type=range_type)
        )

        if not queryset.exists():
            return Response(
                {"status": "error", "message": f"No data available for user {user_id} and range: {range_type}"}
            )

        user_data = self.aggregate_pnl_data(queryset)
        return Response({"status": "success", "data": user_data})

    def aggregate_pnl_data(self, queryset):
        """
        Aggregate PnL data across all users.
        """
        aggregated_data = {
            "estimated_balance": 0,
            "estimated_balance_in_btc": 0,
            "today_pnl": {"usdt": 0, "percentage": 0},
            "pnl_7_days": {"usdt": 0, "percentage": 0},
            "pnl_30_days": {"usdt": 0, "percentage": 0},
            "daily_pnl_chart": {"dates": [], "daily_pnl": []},
            "chart_data": {"dates": [], "cumulative_pnl": [], "net_worth": []},
            "profits": 0,
            "profits_chart_data": {
                "dates": [],
                "daily_profits": [],
                "cumulative_profits": [],
            },
            "asset_allocation": [],
        }

        asset_allocation = defaultdict(lambda: {"value_usd": 0, "percentage": 0})
        daily_pnl_sums = defaultdict(float)
        cumulative_pnl_sums = defaultdict(float)
        net_worth_sums = defaultdict(float)
        daily_profits_sums = defaultdict(float)
        cumulative_profits_sums = defaultdict(float)
        date_set = set()

        for pnl in queryset:
            data = pnl.data
            aggregated_data["estimated_balance"] += data.get("estimated_balance", 0)
            aggregated_data["profits"] += data.get("profits", 0)

            today_pnl = data.get("today_pnl", {})
            aggregated_data["today_pnl"]["usdt"] += today_pnl.get("usdt", 0)
            aggregated_data["today_pnl"]["percentage"] += today_pnl.get("percentage", 0)

            pnl_7_days = data.get("pnl_7_days", {})
            aggregated_data["pnl_7_days"]["usdt"] += pnl_7_days.get("usdt", 0)
            aggregated_data["pnl_7_days"]["percentage"] += pnl_7_days.get("percentage", 0)

            pnl_30_days = data.get("pnl_30_days", {})
            aggregated_data["pnl_30_days"]["usdt"] += pnl_30_days.get("usdt", 0)
            aggregated_data["pnl_30_days"]["percentage"] += pnl_30_days.get("percentage", 0)

            aggregated_data["estimated_balance_in_btc"] += data.get("estimated_balance_in_btc", 0)

            daily_pnl_chart = data.get("daily_pnl_chart", {})
            dates = daily_pnl_chart.get("dates", [])
            daily_pnl = daily_pnl_chart.get("daily_pnl", [])
            for i, date in enumerate(dates):
                daily_pnl_sums[date] += daily_pnl[i]
                date_set.add(date)

            chart_data = data.get("chart_data", {})
            cumulative_pnl = chart_data.get("cumulative_pnl", [])
            net_worth = chart_data.get("net_worth", [])
            for i, date in enumerate(dates):
                cumulative_pnl_sums[date] += cumulative_pnl[i]
                net_worth_sums[date] += net_worth[i]

            profits_chart_data = data.get("profits_chart_data", {})
            daily_profits = profits_chart_data.get("daily_profits", [])
            cumulative_profits = profits_chart_data.get("cumulative_profits", [])
            for i, date in enumerate(dates):
                daily_profits_sums[date] += daily_profits[i]
                cumulative_profits_sums[date] += cumulative_profits[i]

            for asset in data.get("asset_allocation", []):
                asset_name = asset["asset"]
                asset_allocation[asset_name]["value_usd"] += asset["value_usd"]
                asset_allocation[asset_name]["percentage"] += asset["percentage"]

        sorted_dates = sorted(date_set)
        aggregated_data["daily_pnl_chart"]["dates"] = sorted_dates
        aggregated_data["daily_pnl_chart"]["daily_pnl"] = [
            daily_pnl_sums[date] for date in sorted_dates
        ]
        aggregated_data["chart_data"]["dates"] = sorted_dates
        aggregated_data["chart_data"]["cumulative_pnl"] = [
            cumulative_pnl_sums[date] for date in sorted_dates
        ]
        aggregated_data["chart_data"]["net_worth"] = [
            net_worth_sums[date] for date in sorted_dates
        ]
        aggregated_data["profits_chart_data"]["dates"] = sorted_dates
        aggregated_data["profits_chart_data"]["daily_profits"] = [
            daily_profits_sums[date] for date in sorted_dates
        ]
        aggregated_data["profits_chart_data"]["cumulative_profits"] = [
            cumulative_profits_sums[date] for date in sorted_dates
        ]
        aggregated_data["asset_allocation"] = [
            {"asset": asset, "value_usd": data["value_usd"], "percentage": data["percentage"]}
            for asset, data in asset_allocation.items()
        ]

        return aggregated_data
