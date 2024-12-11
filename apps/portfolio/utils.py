from binance.client import Client
import datetime


class PnLDashboardService:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret, tld="com")

    def get_price(self, symbol: str, date: datetime.date):
        """
        Fetch historical price for a given symbol and date.
        """
        try:
            # Convert date to timestamp
            timestamp = int(datetime.datetime(date.year, date.month, date.day).timestamp() * 1000)
            # Get historical price
            klines = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, timestamp,
                                                       timestamp + 86400000)
            if klines:
                return float(klines[0][1]), float(klines[0][4])  # Opening and closing price
            else:
                return None, None
        except Exception as e:
            print(f"Failed to get price for {symbol} on {date}: {e}")
            return None, None

    def get_current_balance(self):
        """
        Fetch current Spot account balances in USD.
        """
        try:
            account_info = self.client.get_account()
            balances = []
            total_usd = 0

            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked

                if total > 0:
                    if asset != "USDT":
                        try:
                            price = float(self.client.get_symbol_ticker(symbol=f"{asset}USDT")["price"])
                            value = total * price
                        except:
                            continue
                    else:
                        value = total

                    balances.append({"asset": asset, "balance": total, "value": value})
                    total_usd += value

            return total_usd, balances
        except Exception as e:
            print(f"Failed to fetch balances: {e}")
            return 0, []

    def calculate_pnl(self, date_range="7d"):
        """
        Calculate PnL, profits, and other metrics for the specified date range.
        """
        try:
            today = datetime.date.today()

            if date_range == "7d":
                start_date = today - datetime.timedelta(days=7)
            elif date_range == "30d":
                start_date = today - datetime.timedelta(days=30)
            else:
                raise ValueError("Invalid date range specified.")

            dates = [today - datetime.timedelta(days=i) for i in range((today - start_date).days + 1)]

            current_balance, balances = self.get_current_balance()

            btc_prices = [self.get_price("BTCUSDT", date) for date in dates]

            daily_pnl = []
            cumulative_pnl = []
            net_worth = []
            daily_profits = []
            cumulative_profits = []
            initial_price = None
            total_profits = 0

            today_pnl = 0
            pnl_7_days = 0
            pnl_30_days = 0

            for i, date in enumerate(dates):
                price_data = btc_prices[i]
                if price_data and price_data[0] is not None and price_data[1] is not None:
                    open_price, close_price = price_data

                    if initial_price is None:
                        initial_price = open_price

                    daily_change = ((close_price - open_price) / open_price) * 100
                    daily_pnl.append(daily_change)

                    cumulative_change = ((close_price - initial_price) / initial_price) * 100
                    cumulative_pnl.append(cumulative_change)

                    proportion = current_balance / btc_prices[-1][1] if btc_prices[-1][1] else 1
                    net_worth.append(close_price * proportion)

                    daily_profit = (close_price - open_price) * proportion
                    daily_profits.append(daily_profit)

                    total_profits += daily_profit
                    cumulative_profits.append(total_profits)

                    if date == today:
                        today_pnl = daily_change

                    if today - datetime.timedelta(days=7) <= date <= today:
                        pnl_7_days += daily_change
                    if today - datetime.timedelta(days=30) <= date <= today:
                        pnl_30_days += daily_change
                else:
                    print(f"Price data missing for date {date}")
                    daily_pnl.append(0)
                    cumulative_pnl.append(cumulative_pnl[-1] if cumulative_pnl else 0)
                    net_worth.append(net_worth[-1] if net_worth else current_balance)

            try:
                btc_usdt_price = float(self.client.get_symbol_ticker(symbol="BTCUSDT")["price"])
                estimated_balance_in_btc = current_balance / btc_usdt_price if btc_usdt_price > 0 else 0
            except Exception as e:
                print(f"Error fetching BTC/USDT price: {e}")
                estimated_balance_in_btc = 0

            filtered_asset_allocation = [
                {
                    "asset": asset["asset"],
                    "value_usd": asset["value"],
                    "percentage": (asset["value"] / current_balance) * 100
                }
                for asset in balances if asset["value"] > 1
            ]

            return {
                "estimated_balance": current_balance,
                "estimated_balance_in_btc": estimated_balance_in_btc,
                "profits": total_profits,
                "today_pnl": today_pnl,
                "pnl_7_days": pnl_7_days,
                "pnl_30_days": pnl_30_days,
                "daily_pnl_chart": {
                    "dates": [date.strftime("%Y-%m-%d") for date in dates],
                    "daily_pnl": daily_pnl
                },
                "chart_data": {
                    "dates": [date.strftime("%Y-%m-%d") for date in dates],
                    "cumulative_pnl": cumulative_pnl,
                    "net_worth": net_worth
                },
                "profits_chart_data": {
                    "dates": [date.strftime("%Y-%m-%d") for date in dates],
                    "daily_profits": daily_profits,
                    "cumulative_profits": cumulative_profits
                },
                "asset_allocation": filtered_asset_allocation
            }
        except Exception as e:
            print(f"Failed to calculate PnL: {e}")
            return {}
