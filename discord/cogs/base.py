import logging
from contextlib import contextmanager
# noinspection PyUnresolvedReferences
from discord.ext import commands
from discord.ext.commands import CheckFailure

import odoo
from odoo import api
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    """所有 Cog 的基礎類別，提供共用的 Odoo 操作方法"""

    # 子類別設定此屬性來指定頻道類型，None 表示不檢查
    channel_type = None

    def __init__(self, bot, db_name: str):
        self.bot = bot
        self._db_name = db_name
        self._channel_cache = {}

    def get_allowed_channels(self, channel_type: str) -> list | None:
        """根據類型從 Odoo 取得允許的頻道列表，失敗時返回 None"""
        if channel_type in self._channel_cache:
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
        except Exception as e:
            _logger.error(f"取得允許頻道失敗: {e}")
            self._channel_cache[channel_type] = None

        return self._channel_cache[channel_type]

    def clear_channel_cache(self):
        """清除頻道快取（設定變更時呼叫）"""
        self._channel_cache = {}

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
