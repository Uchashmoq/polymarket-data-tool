import time
from itertools import islice
from typing import Any, cast

from sortedcontainers import SortedDict


class OrderbookSnapshot:
    __slots__ = (
        "timestamp",
        "local_timestamp",
        "bids_depth",
        "asks_depth",
        "bids",
        "asks",
    )

    def __init__(
        self, timestamp, local_timestamp, bids_depth, asks_depth, bids, asks
    ) -> None:
        self.timestamp = timestamp
        self.local_timestamp = local_timestamp
        self.bids_depth = bids_depth
        self.asks_depth = asks_depth
        self.bids = bids
        self.asks = asks

    def order_equals(self, other: "OrderbookSnapshot") -> bool:
        return (
            self.bids_depth == other.bids_depth
            and self.asks_depth == other.asks_depth
            and self.bids == other.bids
            and self.asks == other.asks
        )

    def get_prices(self) -> tuple[float, float, float, float]:
        best_bid = next(iter(self.bids[0])) if self.bids else 0.0
        best_ask = next(iter(self.asks[0])) if self.asks else 0.0
        return best_bid, best_ask, 0.5 * (best_bid + best_ask), best_ask - best_bid

    def get_bids_depth_vwap(self, depth: int) -> float:
        if depth <= 0:
            return 0.0

        notional = 0.0
        volume = 0.0
        count = 0
        for level in self.bids:
            for price, size in level.items():
                notional += price * size
                volume += size
            count += 1
            if count >= depth:
                break
        return notional / volume if volume > 0.0 else 0.0

    def get_asks_depth_vwap(self, depth: int) -> float:
        if depth <= 0:
            return 0.0

        notional = 0.0
        volume = 0.0
        count = 0
        for level in self.asks:
            for price, size in level.items():
                notional += price * size
                volume += size
            count += 1
            if count >= depth:
                break
        return notional / volume if volume > 0.0 else 0.0

    def get_depth_vwap(self, depth: int) -> tuple[float, float]:
        return self.get_bids_depth_vwap(depth), self.get_asks_depth_vwap(depth)


class Orderbook:
    __slots__ = ("asset_id", "timestamp", "local_timestamp", "bids", "asks")

    def __init__(self, event: dict[str, Any] | None = None):
        self.asset_id = ""
        self.timestamp = 0
        self.local_timestamp = 0
        self.bids = SortedDict()
        self.asks = SortedDict()
        if event is not None:
            self.reset(event)

    def reset(self, event: dict[str, Any]) -> None:
        self.asset_id = event["asset_id"]
        self.timestamp = int(event["timestamp"])
        self.local_timestamp = int(time.time() * 1000)

        bids = self.bids
        asks = self.asks
        bids.clear()
        asks.clear()

        for bid in event["bids"]:
            bids[float(bid["price"])] = float(bid["size"])

        for ask in event["asks"]:
            asks[float(ask["price"])] = float(ask["size"])

    def update(
        self,
        event: dict[str, Any],
        change: dict[str, Any] | None = None,
    ) -> None:
        changes = (change,) if change is not None else event["price_changes"]
        asset_id = self.asset_id
        bids = self.bids
        asks = self.asks
        applied = False

        for item in changes:
            if item is None or item["asset_id"] != asset_id:
                continue

            side = bids if item["side"] == "BUY" else asks
            price = float(item["price"])
            size = float(item["size"])
            if size > 0:
                side[price] = size
            else:
                side.pop(price, None)
            applied = True

        if applied:
            self.timestamp = int(event["timestamp"])
            self.local_timestamp = int(time.time() * 1000)

    def get_prices(self) -> tuple[float, float, float, float]:
        bids = self.bids
        asks = self.asks
        best_bid = cast(float, bids.peekitem(-1)[0]) if bids else 0.0
        best_ask = cast(float, asks.peekitem(0)[0]) if asks else 0.0
        return best_bid, best_ask, 0.5 * (best_bid + best_ask), best_ask - best_bid

    def get_bids_depth_vwap(self, depth: int) -> float:
        if depth <= 0:
            return 0.0

        notional = 0.0
        volume = 0.0
        count = 0
        for price, size in reversed(self.bids.items()):
            notional += price * size
            volume += size
            count += 1
            if count >= depth:
                break
        return notional / volume if volume > 0.0 else 0.0

    def get_asks_depth_vwap(self, depth: int) -> float:
        if depth <= 0:
            return 0.0

        notional = 0.0
        volume = 0.0
        count = 0
        for price, size in self.asks.items():
            notional += price * size
            volume += size
            count += 1
            if count >= depth:
                break
        return notional / volume if volume > 0.0 else 0.0

    def get_depth_vwap(self, depth: int) -> tuple[float, float]:
        return self.get_bids_depth_vwap(depth), self.get_asks_depth_vwap(depth)

    def get_snapshot(self, bids_depth, asks_depth) -> OrderbookSnapshot:

        bids = [
            {cast(float, price): cast(float, size)}
            for price, size in islice(reversed(self.bids.items()), bids_depth)
        ]
        asks = [
            {cast(float, price): cast(float, size)}
            for price, size in islice(self.asks.items(), asks_depth)
        ]

        return OrderbookSnapshot(
            self.timestamp, self.local_timestamp, len(bids), len(asks), bids, asks
        )
