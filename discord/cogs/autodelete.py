import logging
import time

import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)

# 快取過期時間（秒）
CACHE_TTL = 60


class AutodeleteCog(BaseCog):
    """頻道訊息自動刪除"""

    def __init__(self, bot, db_name: str):
        super().__init__(bot, db_name)
        self._autodelete_cache = {}
        self._autodelete_cache_time = 0

    def _is_autodelete_cache_valid(self) -> bool:
        """檢查自動刪除快取是否有效"""
        return (time.time() - self._autodelete_cache_time) < CACHE_TTL

    def get_autodelete_channels(self) -> dict:
        """取得自動刪除頻道設定 {channel_id: delay}"""
        if self._autodelete_cache and self._is_autodelete_cache_valid():
            return self._autodelete_cache

        try:
            with self.odoo_env() as env:
                if 'discord.channel.autodelete' not in env:
                    _logger.warning("discord.channel.autodelete 模型不存在")
                    self._autodelete_cache = {}
                else:
                    self._autodelete_cache = env['discord.channel.autodelete'].get_autodelete_channels()
                self._autodelete_cache_time = time.time()
        except Exception as e:
            _logger.error(f"取得自動刪除頻道設定失敗: {e}")
            self._autodelete_cache = {}
            self._autodelete_cache_time = time.time()

        return self._autodelete_cache

    def clear_autodelete_cache(self):
        """清除自動刪除快取"""
        self._autodelete_cache = {}
        self._autodelete_cache_time = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽所有訊息，處理自動刪除"""
        # 檢查頻道是否在自動刪除清單中
        autodelete_channels = self.get_autodelete_channels()
        channel_id = message.channel.id

        if channel_id not in autodelete_channels:
            return

        config = autodelete_channels[channel_id]
        delay = config['delay']

        if delay <= 0:
            return

        # 判斷是否要刪除此訊息
        should_delete = False

        if message.author.bot:
            # 機器人訊息
            should_delete = config['delete_bot']
        elif isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
            # 管理員訊息
            should_delete = config['delete_admin']
        else:
            # 一般使用者訊息
            should_delete = config['delete_user']

        if not should_delete:
            return

        try:
            await message.delete(delay=delay)
        except Exception as e:
            _logger.warning(f"自動刪除訊息失敗: {e}")
