import logging
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class BuyCog(BaseCog):
    """購買點數相關指令"""

    channel_type = 'buy'

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息，處理動態指令"""
        if message.author.bot:
            return

        # 解析是否為購買指令
        is_match, cmd_name, args = self.parse_command(message.content, 'buy')
        if not is_match:
            return

        # 檢查頻道權限
        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        # 處理指令
        await self._handle_buy(message, args)

    async def _handle_buy(self, message, args):
        """處理購買指令"""
        # 檢查參數
        if len(args) < 1:
            await message.channel.send(f"{message.author.mention} 請指定購買數量，例如: !buy 10")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await message.channel.send(f"{message.author.mention} 數量必須是數字")
            return

        if amount <= 0:
            await message.channel.send(f"{message.author.mention} 購買數量必須大於 0")
            return

        discord_user_id = str(message.author.id)

        try:
            # 產生付款連結
            payment_url = self._generate_payment_url(discord_user_id, amount)

            if not payment_url:
                await message.channel.send(f"{message.author.mention} 系統錯誤，請稍後再試")
                return

            # 私訊給使用者
            await message.author.send(
                f"您要購買 {amount} 點\n"
                f"請點擊以下連結完成付款：\n{payment_url}"
            )
            await message.channel.send(f"{message.author.mention} 付款連結已私訊給您，請查收！")

        except Exception as e:
            _logger.error(f"購買點數失敗: {e}")
            await message.channel.send(f"{message.author.mention} 購買失敗，請稍後再試")

    def _generate_payment_url(self, discord_user_id: str, amount: int) -> str:
        """產生付款連結"""
        try:
            with self.odoo_env() as env:
                base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
                return f"{base_url}/discord/pay?discord_id={discord_user_id}&points={amount}"
        except Exception as e:
            _logger.error(f"產生付款連結失敗: {e}")
            return None
