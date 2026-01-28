import logging
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class BindCog(BaseCog):
    """帳號綁定相關指令"""

    channel_type = 'bind'

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息，處理動態指令"""
        if message.author.bot:
            return

        # 解析是否為綁定指令
        is_match, cmd_name, args = self.parse_command(message.content, 'bind')
        if not is_match:
            return

        # 檢查頻道權限
        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        # 處理指令
        await self._handle_bind(message)

    async def _handle_bind(self, message):
        """處理綁定指令"""
        discord_user_id = str(message.author.id)
        discord_username = message.author.name

        try:
            with self.odoo_env() as env:
                partner = self.get_partner_by_discord_id(env, discord_user_id)

                if partner:
                    await message.channel.send(
                        f"{discord_username} 已經綁定過了！目前有 {partner.points} 點"
                    )
                else:
                    env['res.partner'].sudo().create({
                        'name': discord_username,
                        'discord_id': discord_user_id,
                        'points': 0,
                    })
                    await message.channel.send(f"{discord_username} 綁定成功！")
        except Exception as e:
            _logger.error(f"綁定帳號失敗: {e}")
            await message.channel.send(f"{message.author.mention} 綁定失敗，請稍後再試")
