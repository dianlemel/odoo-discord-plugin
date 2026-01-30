import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class DiscordChannelConfig(models.Model):
    _name = 'discord.channel.config'
    _description = 'Discord 頻道設定'
    _rec_name = 'display_name'

    channel_id = fields.Char(
        string='頻道 ID',
        required=True,
        index=True,
    )
    channel_type = fields.Selection(
        selection='_get_channel_types',
        string='類型',
        required=True,
        index=True,
    )
    name = fields.Char(string='備註')
    display_name = fields.Char(
        string='名稱',
        compute='_compute_display_name',
        store=True,
    )

    @api.model
    def _get_channel_types(self):
        """可用的頻道類型，新增指令時在這裡擴充"""
        return [
            ('bind', '綁定'),
            ('points', '點數查詢'),
            ('buy', '購買點數'),
            ('gift', '贈送點數'),
            ('announce', '群發通知'),
        ]

    @api.depends('channel_id', 'channel_type', 'name')
    def _compute_display_name(self):
        type_dict = dict(self._get_channel_types())
        for record in self:
            type_label = type_dict.get(record.channel_type, record.channel_type)
            if record.name:
                record.display_name = f"[{type_label}] {record.name}"
            else:
                record.display_name = f"[{type_label}] {record.channel_id}"

    _sql_constraints = [
        ('channel_type_unique', 'UNIQUE(channel_id, channel_type)',
         '同一頻道不能重複設定相同類型！'),
    ]

    @api.model
    def get_channels_by_type(self, channel_type: str) -> list:
        """根據類型取得頻道 ID 列表"""
        records = self.sudo().search([('channel_type', '=', channel_type)])
        return [int(r.channel_id) for r in records]

    def _notify_bot_cache_clear(self):
        """通知 Discord Bot 清除頻道快取"""
        try:
            from ..services.discord_bot import discord_bot_service
            discord_bot_service.clear_channel_cache()
            _logger.info("已通知 Discord Bot 清除頻道快取")
        except Exception as e:
            _logger.warning(f"通知 Bot 清除快取失敗: {e}")

    @api.model_create_multi
    def create(self, vals_list):
        """新增時通知 Bot"""
        records = super().create(vals_list)
        self._notify_bot_cache_clear()
        return records

    def write(self, vals):
        """修改時通知 Bot"""
        result = super().write(vals)
        self._notify_bot_cache_clear()
        return result

    def unlink(self):
        """刪除時通知 Bot"""
        result = super().unlink()
        self._notify_bot_cache_clear()
        return result
