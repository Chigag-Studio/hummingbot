import asyncio
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from hummingbot.connector.exchange.alpaca import alpaca_utils
from hummingbot.connector.in_flight_order_base import InFlightOrderBase
from hummingbot.core.event.events import OrderType, TradeType


class AlpacaInFlightOrder(InFlightOrderBase):
    def __init__(self,
                 client_order_id: str,
                 exchange_order_id: Optional[str],
                 trading_pair: str,
                 order_type: OrderType,
                 trade_type: TradeType,
                 price: Decimal,
                 amount: Decimal,
                 initial_state: str = "OPEN"):
        super().__init__(
            client_order_id,
            exchange_order_id,
            trading_pair,
            order_type,
            trade_type,
            price,
            amount,
            initial_state,
        )
        self.trade_id_set = set()
        self.cancelled_event = asyncio.Event()

    @property
    def is_done(self) -> bool:
        return self.last_state in {"new", "partially_filled", "filled", "expired", "canceled"}

    @property
    def is_failure(self) -> bool:
        return self.last_state in {"done_for_day", "expired"}

    @property
    def is_cancelled(self) -> bool:
        return self.last_state in {"canceled", "expired"}

    # @property
    # def order_type_description(self) -> str:
    #     """
    #     :return: Order description string . One of ["limit buy" / "limit sell" / "market buy" / "market sell"]
    #     """
    #     order_type = "market" if self.order_type is OrderType.MARKET else "limit"
    #     side = "buy" if self.trade_type == TradeType.BUY else "sell"
    #     return f"{order_type} {side}"

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> InFlightOrderBase:
        """
        :param data: json data from API
        :return: formatted InFlightOrder
        """
        retval = AlpacaInFlightOrder(
            data["client_order_id"],
            data["id"],
            data["symbol"],
            getattr(OrderType, data["order_type"]),
            getattr(TradeType, data["type"]),
            Decimal(data["filled_avg_price"]),
            Decimal(data["qty"]),
            data["status"]
        )
        retval.executed_amount_base = Decimal(data["executed_amount_base"])
        retval.executed_amount_quote = Decimal(data["executed_amount_quote"])
        #retval.fee_asset = data["fee_asset"]
        #retval.fee_paid = Decimal(data["fee_paid"])
        retval.last_state = data["status"]

        return retval

    def update_with_trade_update_rest(self, trade_update: Dict[str, Any]) -> Tuple[Decimal, Decimal, str]:
        """
        Updates the in flight order with trade update (from trade message REST API)
        return: True if the order gets updated otherwise False
        """
        if Decimal(trade_update["filled_size"]) <= self.executed_amount_base:
            return (0, 0, "")
        trade_id = f'rest_{str(alpaca_utils.get_ms_timestamp())}'
        self.trade_id_set.add(trade_id)

        executed_amount_base = Decimal(trade_update["filled_qty"])
        executed_amount_quote = Decimal(trade_update["notional"])
        delta_trade_amount = executed_amount_base - self.executed_amount_base
        self.executed_amount_base = executed_amount_base
        delta_trade_price = (executed_amount_quote - self.executed_amount_quote) / delta_trade_amount
        self.executed_amount_quote = executed_amount_quote

        return delta_trade_amount, delta_trade_price, trade_id

    def update_with_order_update_ws(self, trade_update: Dict[str, Any]) -> Tuple[Decimal, Decimal, str]:
        """
        Updates the in flight order with trade update (from order message WebSocket API)
        return: True if the order gets updated otherwise False
        """
        if trade_update["last_fill_count"] == '0' or Decimal(trade_update["filled_size"]) <= self.executed_amount_base:
            return (0, 0, "")
        trade_id = f'ws_{str(alpaca_utils.get_ms_timestamp())}'
        self.trade_id_set.add(trade_id)

        executed_amount_base = Decimal(trade_update["filled_size"])
        executed_amount_quote = Decimal(trade_update["filled_notional"])
        delta_trade_amount = executed_amount_base - self.executed_amount_base
        self.executed_amount_base = executed_amount_base
        delta_trade_price = (executed_amount_quote - self.executed_amount_quote) / delta_trade_amount
        self.executed_amount_quote = executed_amount_quote

        return delta_trade_amount, delta_trade_price, trade_id

