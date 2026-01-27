import logging

import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class PointsCog(BaseCog):
    """點數相關指令"""

    channel_type = 'points'

    @commands.command(name="points", help="查詢自己的點數")
    async def check_points(self, ctx):
        """查詢點數指令"""
        discord_user_id = str(ctx.author.id)
        discord_username = ctx.author.name

        try:
            with self.odoo_env() as env:
                partner = self.get_partner_by_discord_id(env, discord_user_id)

                if partner:
                    await ctx.send(f"{discord_username} 目前有 {partner.points} 點")
                else:
                    await ctx.send(f"{discord_username} 尚未綁定帳號，請先綁定！")
        except Exception as e:
            _logger.error(f"查詢點數失敗: {e}")
            await ctx.send("查詢失敗，請稍後再試")
