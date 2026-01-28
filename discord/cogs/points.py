import logging

# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class PointsCog(BaseCog):
    """點數相關指令"""

    channel_type = 'points'

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息，處理動態指令"""
        if message.author.bot:
            return

        # 解析是否為點數查詢指令
        is_match, cmd_name, args = self.parse_command(message.content, 'points')
        if not is_match:
            return

        # 檢查頻道權限
        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        # 處理指令
        await self._handle_points(message)

        # 刪除使用者的指令訊息
        await self.delete_command_message(message)

    async def _handle_points(self, message):
        """處理點數查詢指令"""
        discord_user_id = str(message.author.id)
        discord_username = message.author.name

        try:
            with self.odoo_env() as env:
                partner = self.get_partner_by_discord_id(env, discord_user_id)

                if partner:
                    await message.author.send(f"你目前有 {partner.points} 點")
        except Exception as e:
            _logger.error(f"查詢點數失敗: {e}")
