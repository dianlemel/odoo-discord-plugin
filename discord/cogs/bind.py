import logging
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class BindCog(BaseCog):
    """帳號綁定相關指令"""

    channel_type = 'bind'

    @commands.command(name="bind", help="綁定 Discord 帳號")
    async def bind_account(self, ctx):
        """綁定帳號指令 - 自動建立或更新 partner"""
        discord_user_id = str(ctx.author.id)
        discord_username = ctx.author.name

        try:
            with self.odoo_env() as env:
                partner = self.get_partner_by_discord_id(env, discord_user_id)

                if partner:
                    await ctx.send(
                        f"{discord_username} 已經綁定過了！目前有 {partner.points} 點"
                    )
                else:
                    env['res.partner'].sudo().create({
                        'name': discord_username,
                        'discord_id': discord_user_id,
                        'points': 0,
                    })
                    await ctx.send(f"{discord_username} 綁定成功！")
        except Exception as e:
            _logger.error(f"綁定帳號失敗: {e}")
            await ctx.send("綁定失敗，請稍後再試")
