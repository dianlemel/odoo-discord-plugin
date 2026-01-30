import logging
import re

# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class GiftCog(BaseCog):
    """點數贈送指令"""

    channel_type = 'gift'

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息，處理動態指令"""
        if message.author.bot:
            return

        # 解析是否為贈送指令
        is_match, cmd_name, args = self.parse_command(message.content, 'gift')
        if not is_match:
            return

        # 檢查頻道權限
        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        # 處理指令
        await self._handle_gift(message, args)

    async def _handle_gift(self, message, args):
        """
        處理點數贈送指令

        用法: !gift @用戶 點數 [備註]
        例如: !gift @John 100
              !gift @John 50 感謝幫忙
        """
        sender_discord_id = str(message.author.id)

        # 檢查參數
        if len(args) < 2:
            return

        # 解析接收者（支援 @ mention 格式）
        receiver_arg = args[0]
        # Discord mention 格式: <@123456789> 或 <@!123456789>
        mention_match = re.match(r'<@!?(\d+)>', receiver_arg)
        if not mention_match:
            return

        receiver_discord_id = mention_match.group(1)

        # 解析點數
        try:
            points = int(args[1])
            if points <= 0:
                return
        except ValueError:
            return

        # 解析備註（可選）
        note = ' '.join(args[2:]) if len(args) > 2 else None

        try:
            with self.odoo_env() as env:
                success, msg, gift = env['discord.points.gift'].create_gift(
                    sender_discord_id=sender_discord_id,
                    receiver_discord_id=receiver_discord_id,
                    points=points,
                    note=note,
                )

                if success:
                    # 取得贈送者最新點數
                    sender = self.get_partner_by_discord_id(env, sender_discord_id)

                    result = env['discord.message.template'].render_message_by_type(
                        'gift_success',
                        {
                            'points': points,
                            'receiver': f"<@{receiver_discord_id}>",
                            'remaining_points': sender.points,
                        }
                    )
                    if result:
                        await message.author.send(**result)

                    # 發送公告
                    await self._send_announcement(
                        env,
                        sender_discord_id=sender_discord_id,
                        receiver_discord_id=receiver_discord_id,
                        points=points,
                        note=note,
                    )
                else:
                    # 贈送失敗，私訊錯誤訊息
                    await message.author.send(msg)

        except Exception as e:
            _logger.error(f"贈送點數失敗: {e}")

    async def _send_announcement(self, env, sender_discord_id: str, receiver_discord_id: str, points: int, note: str = None):
        """發送贈送公告到指定頻道"""
        try:
            config = env['ir.config_parameter'].sudo()
            channel_id = config.get_param('discord.gift_announcement_channel')

            if not channel_id:
                return

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                _logger.warning(f"找不到公告頻道: {channel_id}")
                return

            # 使用模板渲染公告
            result = env['discord.message.template'].render_message_by_type(
                'gift_announcement',
                {
                    'sender': f"<@{sender_discord_id}>",
                    'receiver': f"<@{receiver_discord_id}>",
                    'points': points,
                    'note': note,
                }
            )

            if result:
                await channel.send(**result)

        except Exception as e:
            _logger.error(f"發送贈送公告失敗: {e}")
