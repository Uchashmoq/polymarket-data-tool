import time


class Position:
    __slots__ = ("size", "avg_price", "update_time")

    size: float
    avg_price: float
    update_time: int

    def __init__(self, size: float = 0.0, avg_price: float = 0.0, update_time: int = 0):
        self.size = size
        self.avg_price = avg_price
        self.update_time = update_time

    def increase(self, size: float, price: float) -> None:
        old_size = self.size
        new_size = old_size + size
        self.avg_price = (
            (old_size * self.avg_price + size * price) / new_size if old_size else price
        )
        self.size = new_size
        self.update_time = int(time.time() * 1000)

    def decrease(self, size: float) -> None:
        new_size = self.size - size
        if new_size > 0.0:
            self.size = new_size
        else:
            self.size = 0.0
            self.avg_price = 0.0
        self.update_time = int(time.time() * 1000)
