import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class DiscordBotManager(models.AbstractModel):
    """Discord Bot 管理器 - 負責在 Odoo 啟動時啟動 Bot"""
    _name = 'discord.bot.manager'
    _description = 'Discord Bot Manager'

    @api.model
    def _register_hook(self):
        """Odoo 載入模組時自動執行"""
        self._start_bot()

    @api.model
    def _start_bot(self):
        """啟動 Discord Bot"""
        from ..services.discord_bot import discord_bot_service

        # 取得 Bot Token
        token = self.env['ir.config_parameter'].sudo().get_param('discord.bot_token')

        if not token:
            _logger.warning("Discord Bot Token 未設定，請至 設定 > Discord 設定 Bot Token")
            return False

        db_name = self.env.cr.dbname
        discord_bot_service.start(db_name, token)
        return True

    @api.model
    def _stop_bot(self):
        """停止 Discord Bot"""
        from ..services.discord_bot import discord_bot_service
        discord_bot_service.stop()
        return True

    @api.model
    def restart_bot(self):
        """重啟 Discord Bot（可從 Odoo 介面呼叫）"""
        self._stop_bot()
        return self._start_bot()

    @api.model
    def get_bot_status(self):
        """取得 Bot 狀態"""
        from ..services.discord_bot import discord_bot_service
        return {
            'running': discord_bot_service.is_running,
        }
