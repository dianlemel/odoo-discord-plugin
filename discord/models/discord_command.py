import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class DiscordCommandConfig(models.Model):
    _name = 'discord.command.config'
    _description = 'Discord 指令設定'
    _rec_name = 'display_name'

    command_name = fields.Char(
        string='指令名稱',
        required=True,
        help='不含前綴的指令名稱，例如: buy, 購買',
    )
    command_type = fields.Selection(
        selection='_get_command_types',
        string='對應行為',
        required=True,
        index=True,
    )
    description = fields.Char(string='說明')
    display_name = fields.Char(
        string='顯示名稱',
        compute='_compute_display_name',
        store=True,
    )
    active = fields.Boolean(default=True, string='啟用')

    @api.model
    def _get_command_types(self):
        """可用的指令行為類型"""
        return [
            ('bind', '綁定帳號'),
            ('points', '查詢點數'),
            ('buy', '購買點數'),
        ]

    @api.depends('command_name', 'command_type', 'description')
    def _compute_display_name(self):
        type_dict = dict(self._get_command_types())
        for record in self:
            type_label = type_dict.get(record.command_type, record.command_type)
            if record.description:
                record.display_name = f"!{record.command_name} → {type_label} ({record.description})"
            else:
                record.display_name = f"!{record.command_name} → {type_label}"

    _sql_constraints = [
        ('command_name_unique', 'UNIQUE(command_name)',
         '指令名稱不能重複！'),
    ]

    @api.model
    def get_commands_by_type(self, command_type: str) -> list:
        """根據行為類型取得指令名稱列表"""
        records = self.sudo().search([
            ('command_type', '=', command_type),
            ('active', '=', True),
        ])
        return [r.command_name for r in records]

    @api.model
    def get_command_type(self, command_name: str) -> str | None:
        """根據指令名稱取得對應的行為類型"""
        record = self.sudo().search([
            ('command_name', '=', command_name),
            ('active', '=', True),
        ], limit=1)
        return record.command_type if record else None

    @api.model
    def get_all_commands(self) -> dict:
        """取得所有指令對應表 {command_name: command_type}"""
        records = self.sudo().search([('active', '=', True)])
        return {r.command_name: r.command_type for r in records}

    def _notify_bot_cache_clear(self):
        """通知 Discord Bot 清除指令快取"""
        try:
            from ..services.discord_bot import discord_bot_service
            discord_bot_service.clear_command_cache()
            _logger.info("已通知 Discord Bot 清除指令快取")
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
