import asyncio
import logging
import threading

import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

from ..cogs import COGS

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

    def _setup_bot(self, token: str):
        """設定 Discord Bot"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self._bot = commands.Bot(command_prefix="!", intents=intents)

        @self._bot.event
        async def on_ready():
            _logger.info(f"Discord Bot 已上線: {self._bot.user}")
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


# 全域實例
discord_bot_service = DiscordBotService()
