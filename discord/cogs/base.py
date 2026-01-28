import logging
import time
from contextlib import contextmanager
# noinspection PyUnresolvedReferences
from discord.ext import commands
# noinspection PyUnresolvedReferences
from discord.ext.commands import CheckFailure

import odoo
from odoo import api
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

# 快取過期時間（秒）- 設為 60 秒，確保設定變更後最多 60 秒內生效
CACHE_TTL = 60


class BaseCog(commands.Cog):
    """所有 Cog 的基礎類別，提供共用的 Odoo 操作方法"""

    # 子類別設定此屬性來指定頻道類型，None 表示不檢查
    channel_type = None

    def __init__(self, bot, db_name: str):
        self.bot = bot
        self._db_name = db_name
        self._channel_cache = {}
        self._command_cache = {}
        self._cache_time = {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否仍有效"""
        if cache_key not in self._cache_time:
            return False
        return (time.time() - self._cache_time[cache_key]) < CACHE_TTL

    def get_allowed_channels(self, channel_type: str) -> list | None:
        """根據類型從 Odoo 取得允許的頻道列表，失敗時返回 None"""
        cache_key = f'channel_{channel_type}'

        # 檢查快取是否有效
        if channel_type in self._channel_cache and self._is_cache_valid(cache_key):
            return self._channel_cache[channel_type]

        try:
            with self.odoo_env() as env:
                if 'discord.channel.config' not in env:
                    # 模型不存在（模組未升級）
                    _logger.warning("discord.channel.config 模型不存在，跳過頻道檢查")
                    self._channel_cache[channel_type] = None
                else:
                    channels = env['discord.channel.config'].get_channels_by_type(channel_type)
                    self._channel_cache[channel_type] = channels
                self._cache_time[cache_key] = time.time()
        except Exception as e:
            _logger.error(f"取得允許頻道失敗: {e}")
            self._channel_cache[channel_type] = None
            self._cache_time[cache_key] = time.time()

        return self._channel_cache[channel_type]

    def clear_channel_cache(self):
        """清除頻道快取（設定變更時呼叫）"""
        self._channel_cache = {}
        # 只清除頻道相關的快取時間
        for key in list(self._cache_time.keys()):
            if key.startswith('channel_'):
                del self._cache_time[key]

    def clear_command_cache(self):
        """清除指令快取（設定變更時呼叫）"""
        self._command_cache = {}
        # 只清除指令相關的快取時間
        for key in list(self._cache_time.keys()):
            if key.startswith('command_'):
                del self._cache_time[key]

    def get_command_names(self, command_type: str) -> list:
        """根據行為類型從 Odoo 取得指令名稱列表"""
        cache_key = f'command_{command_type}'

        if command_type in self._command_cache and self._is_cache_valid(cache_key):
            return self._command_cache[command_type]

        try:
            with self.odoo_env() as env:
                if 'discord.command.config' not in env:
                    _logger.warning("discord.command.config 模型不存在")
                    self._command_cache[command_type] = []
                else:
                    commands = env['discord.command.config'].get_commands_by_type(command_type)
                    self._command_cache[command_type] = commands
                self._cache_time[cache_key] = time.time()
        except Exception as e:
            _logger.error(f"取得指令設定失敗: {e}")
            self._command_cache[command_type] = []
            self._cache_time[cache_key] = time.time()

        return self._command_cache[command_type]

    def parse_command(self, message_content: str, command_type: str) -> tuple:
        """
        解析訊息是否為指定類型的指令
        返回: (是否匹配, 指令名稱, 參數列表)
        """
        if not message_content.startswith('!'):
            return False, None, []

        parts = message_content[1:].split()
        if not parts:
            return False, None, []

        cmd_name = parts[0].lower()
        args = parts[1:]

        # 檢查是否為此類型的指令
        allowed_commands = self.get_command_names(command_type)
        if cmd_name in [c.lower() for c in allowed_commands]:
            return True, cmd_name, args

        return False, None, []

    async def cog_check(self, ctx):
        """所有指令執行前的檢查 - 驗證頻道"""
        if not self.channel_type:
            return True

        allowed = self.get_allowed_channels(self.channel_type)
        # None 或空列表表示允許全部頻道
        if allowed is None or len(allowed) == 0:
            return True

        return ctx.channel.id in allowed

    async def cog_command_error(self, ctx, error):
        """處理指令錯誤 - 靜默忽略頻道檢查失敗"""
        if isinstance(error, CheckFailure):
            # 頻道不允許，靜默忽略
            return
        # 其他錯誤繼續拋出
        raise error

    @contextmanager
    def odoo_env(self):
        """Context manager 取得 Odoo Environment，自動處理 commit/close"""
        reg = Registry(self._db_name)
        cr = reg.cursor()
        try:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})
            yield env
            cr.commit()
        except Exception:
            cr.rollback()
            raise
        finally:
            cr.close()

    def get_partner_by_discord_id(self, env, discord_user_id: str):
        """透過 Discord User ID 取得關聯的 Partner"""
        return env['res.partner'].sudo().search([
            ('discord_id', '=', discord_user_id)
        ], limit=1)

    def get_command_delete_delay(self) -> int:
        """取得指令自動刪除的秒數"""
        cache_key = 'command_delete_delay'

        if cache_key in self._cache_time and self._is_cache_valid(cache_key):
            return self._command_cache.get(cache_key, 5)

        try:
            with self.odoo_env() as env:
                config = env['ir.config_parameter'].sudo()
                delay = config.get_param('discord.command_delete_delay', '5')
                self._command_cache[cache_key] = int(delay) if delay else 5
                self._cache_time[cache_key] = time.time()
        except Exception as e:
            _logger.error(f"取得指令刪除秒數失敗: {e}")
            self._command_cache[cache_key] = 5
            self._cache_time[cache_key] = time.time()

        return self._command_cache.get(cache_key, 5)

    async def delete_command_message(self, message):
        """刪除使用者的指令訊息"""
        try:
            delay = self.get_command_delete_delay()
            if delay > 0:
                await message.delete(delay=delay)
        except Exception as e:
            _logger.warning(f"刪除指令訊息失敗: {e}")
