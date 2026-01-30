import asyncio
import logging
import threading
import warnings

# 忽略 discord.py 的 DeprecationWarning (aiohttp timeout 參數)
warnings.filterwarnings('ignore', message='.*timeout.*ClientWSTimeout.*', category=DeprecationWarning)

import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

from ..cogs import COGS
from .dm_queue import DMQueue

_logger = logging.getLogger(__name__)


class DiscordBotService:
    """Discord Bot 服務 - 在獨立線程中運行"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._bot = None
        self._thread = None
        self._loop = None
        self._running = False
        self._db_name = None
        # 暫存付款連結訊息資訊，用於付款成功後刪除
        # key: discord_id, value: {'message_id': str, 'channel_id': str}
        self._pending_payment_messages = {}

    def _setup_bot(self, token: str):
        """設定 Discord Bot"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self._bot = commands.Bot(command_prefix="!", intents=intents)

        @self._bot.event
        async def on_ready():
            _logger.info(f"Discord Bot 已上線: {self._bot.user}")
            # 初始化 DM 佇列
            self._bot.dm_queue = DMQueue()
            self._bot.dm_queue.start()
            # 載入所有 Cogs
            await self._load_cogs()

        @self._bot.event
        async def on_message(message):
            if message.author == self._bot.user:
                return
            await self._bot.process_commands(message)

        return token

    async def _load_cogs(self):
        """載入所有 Cogs"""
        for cog_class in COGS:
            try:
                await self._bot.add_cog(cog_class(self._bot, self._db_name))
                _logger.info(f"已載入 Cog: {cog_class.__name__}")
            except Exception as e:
                _logger.error(f"載入 Cog {cog_class.__name__} 失敗: {e}")

    def _run_bot(self, token: str):
        """在獨立線程中運行 Bot"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._bot.start(token))
        except Exception as e:
            _logger.error(f"Discord Bot 執行錯誤: {e}")
        finally:
            self._loop.close()
            self._running = False

    def start(self, db_name: str, token: str):
        """啟動 Discord Bot 服務"""
        if self._running:
            _logger.warning("Discord Bot 已在運行中")
            return

        if not token:
            _logger.warning("未設定 Discord Bot Token，跳過啟動")
            return

        self._db_name = db_name
        self._setup_bot(token)
        self._running = True

        self._thread = threading.Thread(
            target=self._run_bot,
            args=(token,),
            daemon=True,
            name="DiscordBotThread"
        )
        self._thread.start()
        _logger.info("Discord Bot 服務已啟動")

    def stop(self):
        """停止 Discord Bot 服務"""
        if not self._running:
            return

        if self._bot and self._loop:
            # 停止 DM 佇列
            if hasattr(self._bot, 'dm_queue'):
                self._bot.dm_queue.stop()
            asyncio.run_coroutine_threadsafe(self._bot.close(), self._loop)

        self._running = False
        _logger.info("Discord Bot 服務已停止")

    @property
    def is_running(self):
        return self._running

    def clear_channel_cache(self):
        """清除所有 Cog 的頻道快取"""
        if not self._bot:
            return

        for cog in self._bot.cogs.values():
            if hasattr(cog, 'clear_channel_cache'):
                cog.clear_channel_cache()
        _logger.info("已清除所有 Cog 的頻道快取")

    def clear_command_cache(self):
        """清除所有 Cog 的指令快取"""
        if not self._bot:
            return

        for cog in self._bot.cogs.values():
            if hasattr(cog, 'clear_command_cache'):
                cog.clear_command_cache()
        _logger.info("已清除所有 Cog 的指令快取")

    def clear_autodelete_cache(self):
        """清除自動刪除頻道快取"""
        if not self._bot:
            return

        for cog in self._bot.cogs.values():
            if hasattr(cog, 'clear_autodelete_cache'):
                cog.clear_autodelete_cache()
        _logger.info("已清除自動刪除頻道快取")

    def store_pending_payment_message(self, discord_id: str, message_id: str, channel_id: str):
        """
        暫存付款連結訊息資訊

        :param discord_id: Discord 用戶 ID
        :param message_id: 訊息 ID
        :param channel_id: 頻道 ID
        """
        self._pending_payment_messages[discord_id] = {
            'message_id': message_id,
            'channel_id': channel_id,
        }
        _logger.info(f"已暫存付款連結訊息: discord_id={discord_id}, message_id={message_id}")

    def get_pending_payment_message(self, discord_id: str) -> dict | None:
        """
        取得並移除暫存的付款連結訊息資訊

        :param discord_id: Discord 用戶 ID
        :return: {'message_id': str, 'channel_id': str} 或 None
        """
        return self._pending_payment_messages.pop(discord_id, None)

    def schedule_payment_notification(self, discord_id: str, send_kwargs: dict,
                                       payment_message_id: str = None,
                                       payment_channel_id: str = None):
        """
        排程付款成功通知

        :param discord_id: Discord 用戶 ID
        :param send_kwargs: 傳給 user.send() 的 kwargs dict
        :param payment_message_id: 原付款連結訊息 ID（用於刪除）
        :param payment_channel_id: 原付款連結頻道 ID（用於刪除）
        """
        if not self._running or not self._loop or not self._bot:
            _logger.warning("Discord Bot 未運行，無法排程付款通知")
            return

        asyncio.run_coroutine_threadsafe(
            self._send_payment_notification(
                discord_id, send_kwargs, payment_message_id, payment_channel_id
            ),
            self._loop
        )

    async def _send_payment_notification(self, discord_id: str, send_kwargs: dict,
                                          payment_message_id: str = None,
                                          payment_channel_id: str = None):
        """
        發送付款成功通知並刪除原付款連結訊息

        :param discord_id: Discord 用戶 ID
        :param send_kwargs: 傳給 user.send() 的 kwargs dict
        :param payment_message_id: 原付款連結訊息 ID（用於刪除）
        :param payment_channel_id: 原付款連結頻道 ID（用於刪除）
        """
        try:
            # 取得用戶
            user = await self._bot.fetch_user(int(discord_id))
            if not user:
                _logger.warning(f"找不到 Discord 用戶: {discord_id}")
                return

            # 透過 DM 佇列發送付款成功通知
            future = await self._bot.dm_queue.enqueue(user, **send_kwargs)
            await future
            _logger.info(f"已發送付款通知給用戶 {discord_id}")

            # 刪除原付款連結訊息
            if payment_message_id and payment_channel_id:
                try:
                    channel = await self._bot.fetch_channel(int(payment_channel_id))
                    if channel:
                        original_message = await channel.fetch_message(int(payment_message_id))
                        if original_message:
                            await original_message.delete()
                            _logger.info(f"已刪除原付款連結訊息 {payment_message_id}")
                except discord.NotFound:
                    _logger.warning(f"找不到原付款連結訊息 {payment_message_id}，可能已被刪除")
                except discord.Forbidden:
                    _logger.warning(f"無權限刪除訊息 {payment_message_id}")
                except Exception as e:
                    _logger.error(f"刪除原付款連結訊息失敗: {e}")

        except discord.NotFound:
            _logger.warning(f"找不到 Discord 用戶: {discord_id}")
        except discord.Forbidden:
            _logger.warning(f"無法私訊用戶 {discord_id}，可能已關閉私訊")
        except Exception as e:
            _logger.error(f"發送付款通知失敗: {e}")


# 全域實例
discord_bot_service = DiscordBotService()
