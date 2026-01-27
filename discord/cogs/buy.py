import logging
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class BuyCog(BaseCog):
    """購買點數相關指令"""

    channel_type = 'buy'

    @commands.command(name="buy", help="購買點數，例如: !buy 10")
    async def buy_points(self, ctx, amount: int):
        """購買點數指令 - 私訊付款連結給使用者"""
        if amount <= 0:
            await ctx.send("購買數量必須大於 0")
            return

        discord_user_id = str(ctx.author.id)

        try:
            # 產生付款連結
            payment_url = self._generate_payment_url(discord_user_id, amount)

            if not payment_url:
                await ctx.send("系統錯誤，請稍後再試")
                return

            # 私訊給使用者
            await ctx.author.send(
                f"您要購買 {amount} 點\n"
                f"請點擊以下連結完成付款：\n{payment_url}"
            )
            await ctx.send(f"{ctx.author.mention} 付款連結已私訊給您，請查收！")

        except Exception as e:
            _logger.error(f"購買點數失敗: {e}")
            await ctx.send("購買失敗，請稍後再試")

    def _generate_payment_url(self, discord_user_id: str, amount: int) -> str:
        """產生付款連結"""
        try:
            with self.odoo_env() as env:
                base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
                return f"{base_url}/discord/pay?discord_id={discord_user_id}&points={amount}"
        except Exception as e:
            _logger.error(f"產生付款連結失敗: {e}")
            return None
