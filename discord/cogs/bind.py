import base64
import logging

import aiohttp
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

    async def _fetch_avatar(self, user) -> str | None:
        """取得使用者頭像並轉為 base64"""
        try:
            avatar = user.display_avatar
            if not avatar:
                return None

            async with aiohttp.ClientSession() as session:
                async with session.get(avatar.url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            _logger.warning(f"取得頭像失敗: {e}")
        return None

    async def _handle_bind(self, message):
        """處理綁定指令"""
        discord_user_id = str(message.author.id)
        discord_username = message.author.name

        try:
            # 先取得頭像
            avatar_base64 = await self._fetch_avatar(message.author)

            with self.odoo_env() as env:
                partner = self.get_partner_by_discord_id(env, discord_user_id)

                if partner:
                    bound_msg = env['discord.message.template'].render_by_type(
                        'bind_already_bound', {'points': partner.points}
                    )
                    if bound_msg:
                        await message.author.send(bound_msg)
                else:
                    vals = {
                        'name': discord_username,
                        'discord_id': discord_user_id,
                        'points': 0,
                    }
                    if avatar_base64:
                        vals['image_1920'] = avatar_base64

                    env['res.partner'].sudo().create(vals)
                    success_msg = env['discord.message.template'].render_by_type(
                        'bind_success', {}
                    )
                    if success_msg:
                        await message.author.send(success_msg)
        except Exception as e:
            _logger.error(f"綁定帳號失敗: {e}")
