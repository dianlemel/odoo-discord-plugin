import logging
import re

# noinspection PyUnresolvedReferences
from discord.ext import commands

from .base import BaseCog

_logger = logging.getLogger(__name__)


class AnnounceCog(BaseCog):
    """群發通知指令"""

    channel_type = 'announce'

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息，處理群發通知指令"""
        if message.author.bot:
            return

        # 解析是否為 announce 指令
        is_match, cmd_name, args = self.parse_command(message.content, 'announce')
        if not is_match:
            return

        # 檢查頻道權限
        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        await self._handle_announce(message, args)

    async def _handle_announce(self, message, args):
        """
        處理群發通知指令

        用法: !announce @Role 訊息內容
        """
        if not args:
            return

        # 解析身分組 mention（格式: <@&role_id>）
        role_match = re.match(r'<@&(\d+)>', args[0])
        if not role_match:
            return

        role_id = int(role_match.group(1))

        # 取得訊息內容（身分組之後的部分）
        announce_message = ' '.join(args[1:]).strip()
        if not announce_message:
            return

        # 檢查發送者是否有允許的身分組
        has_permission = await self._check_permission(message)
        if not has_permission:
            _logger.warning(f"使用者 {message.author} 無權使用 announce 指令")
            return

        # 取得身分組物件
        guild = message.guild
        if not guild:
            return

        role = guild.get_role(role_id)
        if not role:
            _logger.warning(f"找不到身分組: {role_id}")
            return

        # 預先渲染模板（只查一次 DB）
        try:
            with self.odoo_env() as env:
                announce_result = env['discord.message.template'].render_message_by_type(
                    'announce',
                    {
                        'message': announce_message,
                        'role_name': role.name,
                        'sender': f"<@{message.author.id}>",
                        'guild_name': guild.name,
                    }
                )
        except Exception as e:
            _logger.error(f"渲染群發通知模板失敗: {e}")
            return

        if not announce_result:
            _logger.warning("找不到 announce 模板或渲染失敗")
            return

        # 逐一私訊成員
        members = [m for m in role.members if not m.bot]
        total = len(members)
        success = 0
        failed = 0

        for member in members:
            try:
                await member.send(**announce_result)
                success += 1
            except Exception as e:
                _logger.error(f"發送群發通知給 {member} 失敗: {e}")
                failed += 1

        # 回報結果給發送者
        try:
            with self.odoo_env() as env:
                result = env['discord.message.template'].render_message_by_type(
                    'announce_result',
                    {
                        'role_name': role.name,
                        'total': total,
                        'success': success,
                        'failed': failed,
                    }
                )
            if result:
                await message.author.send(**result)
        except Exception as e:
            _logger.error(f"發送群發結果通知失敗: {e}")

    async def _check_permission(self, message) -> bool:
        """檢查發送者是否擁有允許使用 announce 的身分組"""
        try:
            with self.odoo_env() as env:
                config = env['ir.config_parameter'].sudo()
                allowed_roles_str = config.get_param('discord.announce_allowed_roles', '')

            if not allowed_roles_str:
                # 未設定允許身分組，不允許任何人使用
                return False

            allowed_role_ids = [
                int(r.strip()) for r in allowed_roles_str.split(',') if r.strip()
            ]

            if not allowed_role_ids:
                return False

            # 檢查發送者是否擁有任一允許的身分組
            member_role_ids = [role.id for role in message.author.roles]
            return any(rid in member_role_ids for rid in allowed_role_ids)

        except Exception as e:
            _logger.error(f"檢查 announce 權限失敗: {e}")
            return False
