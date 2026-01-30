import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum

import discord

_logger = logging.getLogger(__name__)

# 序列計數器，確保同優先度時按 FIFO 排序
_sequence_counter = 0


def _next_sequence():
    global _sequence_counter
    _sequence_counter += 1
    return _sequence_counter


class DMPriority(IntEnum):
    """DM 優先度（數值越小越優先）"""
    NORMAL = 0
    LOW = 10


@dataclass(order=True)
class DMRequest:
    """佇列中的 DM 請求"""
    priority: int
    sequence: int
    recipient: discord.abc.Snowflake = field(compare=False)
    kwargs: dict = field(compare=False)
    future: asyncio.Future = field(compare=False)


class DMQueue:
    """
    集中式 DM 佇列

    所有私訊透過此佇列發送，支援優先度排序與速率限制。
    """

    def __init__(self, rate_limit: int = 5, rate_period: float = 5.0):
        """
        :param rate_limit: 時間窗口內允許的最大發送數量
        :param rate_period: 時間窗口長度（秒）
        """
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._task: asyncio.Task | None = None
        # Token Bucket 參數
        self._rate_limit = rate_limit
        self._rate_period = rate_period
        self._tokens = float(rate_limit)
        self._last_refill = time.monotonic()

    async def enqueue(self, recipient, priority=DMPriority.NORMAL, **kwargs) -> asyncio.Future:
        """
        將 DM 請求加入佇列

        :param recipient: 接收者（discord.User / discord.Member）
        :param priority: 優先度
        :param kwargs: 傳給 recipient.send() 的參數
        :return: Future，await 後取得 send() 的回傳值
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        request = DMRequest(
            priority=int(priority),
            sequence=_next_sequence(),
            recipient=recipient,
            kwargs=kwargs,
            future=future,
        )
        await self._queue.put(request)
        return future

    def start(self):
        """啟動佇列消費者"""
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._process())
        _logger.info("DM 佇列處理器已啟動")

    def stop(self):
        """停止佇列消費者"""
        if self._task is not None:
            self._task.cancel()
            self._task = None
            _logger.info("DM 佇列處理器已停止")

    async def _wait_for_token(self):
        """Token Bucket 速率限制：等待直到有可用 token"""
        while True:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                float(self._rate_limit),
                self._tokens + elapsed * (self._rate_limit / self._rate_period),
            )
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            # 計算需等待多久才有 1 個 token
            wait = (1.0 - self._tokens) / (self._rate_limit / self._rate_period)
            await asyncio.sleep(wait)

    async def _process(self):
        """持續從佇列取出並發送 DM"""
        try:
            while True:
                request: DMRequest = await self._queue.get()

                await self._wait_for_token()

                try:
                    result = await request.recipient.send(**request.kwargs)
                    if not request.future.done():
                        request.future.set_result(result)
                except discord.HTTPException as e:
                    if e.status == 429:
                        # 速率限制，等待 retry_after 後重新入佇
                        retry_after = getattr(e, 'retry_after', 5.0) or 5.0
                        _logger.warning(f"DM 速率限制，{retry_after:.1f} 秒後重試")
                        await asyncio.sleep(retry_after)
                        # 重新入佇（不消耗新序號，維持原排序）
                        await self._queue.put(request)
                    else:
                        _logger.error(f"發送 DM 給 {request.recipient} 失敗: {e}")
                        if not request.future.done():
                            request.future.set_exception(e)
                except Exception as e:
                    _logger.error(f"發送 DM 給 {request.recipient} 失敗: {e}")
                    if not request.future.done():
                        request.future.set_exception(e)
                finally:
                    self._queue.task_done()

        except asyncio.CancelledError:
            _logger.info("DM 佇列處理器已取消")
