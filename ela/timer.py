import asyncio
import functools
from time import time
from typing import Awaitable


class Timer:
    def __init__(self, *, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self._loop = loop

        self._transaction_count = 0
        self._used_time = 0.0

    @property
    def transaction_count(self) -> int:
        return self._transaction_count

    @property
    def used_time(self) -> float:
        return self._used_time

    @property
    def average_process_time(self) -> float:
        try:
            return self._used_time / self._transaction_count
        except ZeroDivisionError:
            return 0.0

    def _calc_used_time(self, real_time: float, _task):
        # loop_time_calc, real_time_calc = self._loop.time() - loop_time, time() - real_time
        self._used_time += time() - real_time
        self._transaction_count += 1

    def executor(self, coro: Awaitable):
        real_time = time()
        self._loop.create_task(coro).add_done_callback(
            functools.partial(self._calc_used_time, real_time)
        )
