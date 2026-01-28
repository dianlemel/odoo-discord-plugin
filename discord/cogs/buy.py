import logging

import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class PaymentView(discord.ui.View):
    """付款按鈕視圖"""

    def __init__(self, payment_url: str, points: int):
        super().__init__(timeout=None)  # 不過期
        self.add_item(discord.ui.Button(
            label=f"💳 點擊付款 ({points} 點)",
            url=payment_url,
            style=discord.ButtonStyle.link
        ))


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
            return

        try:
            amount = int(args[0])
        except ValueError:
            return

        if amount <= 0:
            return

        discord_user_id = str(message.author.id)

        try:
            # 產生付款連結
            payment_url = self._generate_payment_url(discord_user_id, amount)

            if not payment_url:
                return

            # 私訊給使用者（使用按鈕）
            dm_message = await message.author.send(
                f"你要購買 **{amount}** 點\n請點擊下方按鈕完成付款：",
                view=PaymentView(payment_url, amount)
            )

            # 暫存訊息資訊，用於付款成功後刪除
            self._store_payment_message_info(
                discord_user_id,
                str(dm_message.id),
                str(dm_message.channel.id)
            )

        except Exception as e:
            _logger.error(f"購買點數失敗: {e}")

    def _generate_payment_url(self, discord_user_id: str, amount: int) -> str | None:
        """產生付款連結"""
        try:
            with self.odoo_env() as env:
                base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
                return f"{base_url}/discord/pay?discord_id={discord_user_id}&points={amount}"
        except Exception as e:
            _logger.error(f"產生付款連結失敗: {e}")
            return None

    def _store_payment_message_info(self, discord_user_id: str, message_id: str, channel_id: str):
        """
        暫存付款連結訊息資訊到 bot service

        當訂單建立時會從這裡取得訊息資訊並存入訂單
        """
        try:
            from ..services.discord_bot import discord_bot_service
            discord_bot_service.store_pending_payment_message(
                discord_user_id, message_id, channel_id
            )
        except Exception as e:
            _logger.error(f"暫存付款連結訊息資訊失敗: {e}")
