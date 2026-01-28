from odoo import api, fields, models


class DiscordChannelAutodelete(models.Model):
    _name = 'discord.channel.autodelete'
    _description = 'Discord 頻道自動刪除設定'
    _order = 'channel_name'

    channel_id = fields.Char('頻道 ID', required=True, index=True)
    channel_name = fields.Char('頻道名稱', help='方便辨識用，非必填')
    delete_delay = fields.Integer('刪除延遲（秒）', default=5, required=True)
    delete_admin = fields.Boolean('刪除管理員訊息', default=False)
    delete_bot = fields.Boolean('刪除機器人訊息', default=False)
    delete_user = fields.Boolean('刪除一般使用者訊息', default=True)
    active = fields.Boolean('啟用', default=True)

    _sql_constraints = [
        ('channel_id_unique', 'UNIQUE(channel_id)', '此頻道已存在！'),
    ]

    def get_autodelete_channels(self):
        """取得所有啟用的自動刪除頻道設定"""
        channels = self.sudo().search([('active', '=', True)])
        return {
            int(ch.channel_id): {
                'delay': ch.delete_delay,
                'delete_admin': ch.delete_admin,
                'delete_bot': ch.delete_bot,
                'delete_user': ch.delete_user,
            }
            for ch in channels
        }

    def _notify_bot_cache_clear(self):
        """通知 Bot 清除自動刪除快取"""
        from ..services.discord_bot import discord_bot_service
        if discord_bot_service.is_running:
            discord_bot_service.clear_autodelete_cache()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._notify_bot_cache_clear()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._notify_bot_cache_clear()
        return result

    def unlink(self):
        result = super().unlink()
        self._notify_bot_cache_clear()
        return result
